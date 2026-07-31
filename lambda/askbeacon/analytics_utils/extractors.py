import contextlib
import io
import json
from copy import copy
from typing import Dict, List

import black
import joblib
from shared.utils import ENV_ATHENA
from smart_open import open as sopen
from utils.db import search_db
from utils.models import (
    AggregationEnum,
    FilterTypeEnum,
    GranularityEnum,
    SheepScopeEnum,
    to_beacon_scope,
)
from shared.sheep_schema import DEFAULT_ASSEMBLY_ID
from utils.sanitisers import sanitise
from utils.templates import get_data_extractor_map_chain

from .beacon_sdk import BeaconV2 as _BeaconV2
from .beacon_sdk import normalise_response

def get_var_name(var, env):
    for name, value in env.items():
        if value is var:
            return name


def get_table_summary(data: List[Dict]):
    if not data:
        return [], []

    table_col_names = list(data[0].keys())
    table_col_types = [None] * len(table_col_names)

    for row in data:
        for col, val in enumerate(row.values()):
            typ = type(val).__name__
            if table_col_types[col] is None or typ != "str":
                table_col_types[col] = typ

    return table_col_names, table_col_types


def _as_int_list(value, default):
    """Beacon wants start/end as lists of ints."""
    if isinstance(value, list) and value:
        try:
            return [int(v) for v in value]
        except (TypeError, ValueError):
            return default
    if isinstance(value, int):
        return [value]
    if isinstance(value, str) and value.isdigit():
        return [int(value)]
    return default


def generate_extractor_code(job_id: str, query: str) -> str:
    extracted_data = get_data_extractor_map_chain().invoke(query)
    print(f"{extracted_data=}")

    scope = extracted_data["scope"].scope
    region = extracted_data["region"]
    granularity = extracted_data["granularity"].granularity
    aggregation = extracted_data["aggregation"]

    sdk_lines = []
    sdk_comments = []

    # ------------------------------------------------------------------ scope
    beacon_scope = to_beacon_scope(scope)
    if scope != SheepScopeEnum.UNKNOWN:
        sdk_lines.append(f'.with_scope("{beacon_scope.value}")')
        sdk_comments.append(
            f"# Question is about '{scope.value}' -> Beacon scope '{beacon_scope.value}'."
        )
    else:
        sdk_lines.append(".with_scope('<ENTER YOUR SCOPE>')")
        sdk_comments.append("# Could not decide a scope for your query.")

    # ----------------------------------------------------------------- region
    if region.success:
        start = _as_int_list(region.start, [0])
        # end must be >= 1 per g-variants-request-parameters.json, so it can
        # never simply mirror a start of 0.
        end = _as_int_list(region.end, None) or [max(start[-1], 1)]
        chromosome = region.chromosome if region.chromosome != "unknown" else "1"
        sdk_lines.append(
            f'.with_region("{chromosome}", {start[0]}, {end[-1]})'
        )
        sdk_comments.append(
            f"# Region detected: chromosome {chromosome}, {start[0]}-{end[-1]}."
        )
        if region.snp_ids:
            markers = ", ".join(region.snp_ids)
            sdk_comments.append(f"# Marker names mentioned: {markers}")

    # ---------------------------------------------------------------- filters
    ontology_terms = []
    for fil in extracted_data["filters"].filters:
        if not fil.is_resolvable():
            sdk_comments.append(
                f"# Ignored condition '{fil.field or fil.term}': no matching column."
            )
            continue

        filter_scope = to_beacon_scope(fil.scope).value
        if fil.type == FilterTypeEnum.ONTOLOGY:
            term = fil.term or fil.value
            for entry, score in search_db(term):
                ontology_terms.append((term, entry.term, entry.label))
                sdk_lines.append(
                    f".with_filter('ontology', '{entry.term}', '{filter_scope}')"
                )
                sdk_comments.append(f"# {term} -> {entry.term} ({entry.label})")
        else:
            field = fil.resolved_field
            sdk_lines.append(
                f".with_filter('alphanumeric', '{field}', '{filter_scope}', "
                f"'{fil.operator.value}', '{fil.value}')"
            )
            sdk_comments.append(f"# Condition: {fil.describe()}")

    # ------------------------------------------------------------ granularity
    # Records are always requested: the analytics step needs rows to compute
    # frequencies, and a count is trivially derived from them.
    if granularity == GranularityEnum.COUNT:
        sdk_comments.append("# You asked for a count - len(dataframes[0]) gives it.")
    elif granularity == GranularityEnum.BOOLEAN:
        sdk_comments.append("# You asked whether anything matches at all.")

    if aggregation.aggregation != AggregationEnum.NONE:
        group_by = ", ".join(aggregation.group_by) or "no grouping"
        sdk_comments.append(
            f"# Follow-up statistic requested: {aggregation.aggregation.value} ({group_by})."
        )

    sdk_construct = (
        "data = BeaconV2()" + "".join(sdk_lines) + ".load()\n\n"
        "\n".join(sdk_comments)
        + "\n\n# Please update this line with other dataframes"
        + "\ndataframes = [data]\n"
    )

    sdk_construct = black.format_str(sdk_construct, mode=black.FileMode())

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/generated_extract.py",
        "w",
    ) as fo:
        fo.write(sdk_construct)

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/extraction_query.txt",
        "w",
    ) as fo:
        fo.write(query)

    return sdk_construct


def run_extractors(job_id: str, url: str, header: str, code: str) -> Dict:
    BeaconV2 = lambda: _BeaconV2(url, header)  # noqa: E731 - injected into exec scope
    exec_globals = copy(globals())
    exec_globals["BeaconV2"] = BeaconV2
    exec_globals["os"] = None
    exec_globals["sys"] = None

    std_output = io.StringIO()
    std_error = io.StringIO()
    success = False
    result_dataframes_json = []
    result_dataframes_pandas = []
    dataframe_names = []

    # We must not use any overlapping variable names: variables in the global
    # scope above are not overwritten by exec, so re-declaring e.g.
    # `dataframes = []` here would leave the user's assignment invisible.
    with contextlib.redirect_stdout(std_output), contextlib.redirect_stderr(std_error):
        try:
            code = sanitise(code)
            exec(code, exec_globals, locals())
            computed_dataframes = locals().get("dataframes", None)

            if not isinstance(computed_dataframes, list):
                raise ValueError(
                    "The variable 'dataframes' was not defined or was not a list!"
                )

            snapshot = copy(locals())
            dataframe_names = [get_var_name(x, snapshot) for x in computed_dataframes]
            print("Dataframe names", dataframe_names)

            normalised = [normalise_response(df) for df in computed_dataframes]
            result_dataframes_pandas = [item[0] for item in normalised]
            result_dataframes_json = [item[1] for item in normalised]
            success = True
        except Exception as e:  # noqa: BLE001 - surfaced to the user via stderr
            print(f"Exception: {e}", file=std_error)

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/extracted.pkl.bz2",
            "wb",
        ) as fo:
            joblib.dump(result_dataframes_pandas, fo, 3)

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/extract.py",
            "w",
        ) as fo:
            fo.write(code)

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/metadata.json",
            "w",
        ) as fo:
            metadata = {
                "table_names": dataframe_names,
                "table_metadata": [
                    get_table_summary(dataframe) for dataframe in result_dataframes_json
                ],
            }
            json.dump(metadata, fo)

    result = {
        "dataframes": result_dataframes_json,
        "success": success,
        "stdout": std_output.getvalue(),
        "stderr": std_error.getvalue(),
    }

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/extraction_result.json",
        "w",
    ) as fo:
        json.dump(result, fo)

    return result
