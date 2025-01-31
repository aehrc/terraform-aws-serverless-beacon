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
from utils.models import Scope, ScopeEnum
from utils.sanitisers import sanitise
from utils.templates import get_data_extractor_map_chain

from .beacon_sdk import BeaconV2 as _BeaconV2
from .beacon_sdk import normalise_response


def get_var_name(var, env):
    for name, value in env.items():
        if value is var:
            return name


def get_table_summary(data: List[Dict]):
    table_col_names = list(data[0].keys())
    table_col_types = [None] * len(table_col_names)

    for row in data:
        types = [type(val) for val in row.values()]
        for col, typ in enumerate(types):
            if table_col_types[col] is None:
                # we want the types to be JSON serialisable
                table_col_types[col] = typ.__name__
            elif typ is not str:
                # we want the types to be JSON serialisable
                table_col_types[col] = typ.__name__

    return table_col_names, table_col_types


def generate_extractor_code(job_id: str, query: str) -> Dict:
    extractor_chain = get_data_extractor_map_chain()
    extracted_data = extractor_chain.invoke(query)

    print(f"{extracted_data=}")
    print(f"filters text: {extracted_data["filters"].filters}")

    if len(extracted_data["filters"].filters) > 0:
        filters = extracted_data["filters"]
        filters = filters.model_dump(mode="json")["filters"]
        hits = []

        for fil in filters:
            entries = search_db(fil["term"])
            for entry, score in entries:
                hits.append(
                    {
                        "scope": fil["scope"],
                        "term": entry.term,
                        "score": score,
                        "label": entry.label,
                        "query": fil["term"],
                    }
                )
        extracted_data["filters"] = hits
        print(f"filters coded: {hits}")
    else:
        extracted_data["filters"] = []

    sdk_construct = "data = BeaconV2()"
    sdk_comments = ""

    scope = extracted_data.get("scope", Scope(scope=ScopeEnum.UNKNOWN))
    filters = extracted_data["filters"]

    if extracted_data["variant"].success:
        sdk_comments += f"""# Variants detected in the query.\n"""
        sdk_construct += f""".with_g_variant("""
        print(f"variant found: {extracted_data["variant"].dict()}")
        assembly_id = extracted_data["variant"].assembly_id
        sdk_construct += "'GRCH38'" if assembly_id == "unknown" else f"'{assembly_id}'"
        sdk_construct += ",'N','N',"
        start = extracted_data["variant"].start
        if isinstance(start, list):
            sdk_construct += "[0]," if start == "unknown" else f"{start},"
        else:
            sdk_construct += "[0]," if start == "unknown" else f"[{start}],"
        end = extracted_data["variant"].end
        if isinstance(end, list):
            sdk_construct += "[0]," if end == "unknown" else f"{end},"
        else:
            sdk_construct += "[0]," if end == "unknown" else f"[{end}],"
        reference_name = extracted_data["variant"].chromosome
        sdk_construct += "'1'" if reference_name == "unknown" else f"'{reference_name}'"
        sdk_construct += ")"

    if scope.scope != ScopeEnum.UNKNOWN:
        print(f"{scope=}")
        scope = scope.model_dump(mode="json")["scope"]
        sdk_construct += f""".with_scope("{scope}")"""
        sdk_comments += f"""# Scope detected to be '{scope}'.\n"""
    else:
        sdk_comments += f"""# Could not decide a scope for your query.\n"""
        sdk_construct += f""".with_scope('<ENTER YOUR SCOPE>')"""

    for fil in filters:
        print(f"{fil=}")
        sdk_comments += f"""# {fil["term"]} -> '{fil["label"]}'\n"""
        sdk_construct += (
            f""".with_filter('ontology', '{fil["term"]}', '{fil["scope"]}') """
        )

    sdk_construct = (
        sdk_construct
        + ".load()"
        + "\n\n"
        + sdk_comments
        + "\n# Please update this line with other dataframes"
        + "\ndataframes = [data]"
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


def run_extractors(
    job_id: str,
    url: str,
    header: str,
    code: str,
) -> Dict:
    BeaconV2 = lambda: _BeaconV2(url, header)
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

    # We must not use any overlapping variable names
    # variables in the global scpope (above) will not be overwritten
    # if we do that; which means they will remain empty even after edits
    # to reproduce try declaring an empty array dataframes = []
    # this breaks the whole thing
    with contextlib.redirect_stdout(std_output), contextlib.redirect_stderr(std_error):
        try:
            code = sanitise(code)
            exec(code, exec_globals, locals())
            computed_dataframes = locals().get("dataframes", None)

            if not isinstance(computed_dataframes, list):
                raise ValueError(
                    "The variable 'dataframes' was not defined or was not a list!"
                )

            # take a snapshot because we do not want x to appear there
            # this should be a shallow copy to prevent memory address changes
            snapshot = copy(locals())
            dataframe_names = [
                get_var_name(x, snapshot) for x in locals()["dataframes"]
            ]
            print("Dataframe names", dataframe_names)

            # print(f"{dataframe_names}")

            normalised_dataframes = [
                normalise_response(computed_dataframe)
                for computed_dataframe in computed_dataframes
            ]
            result_dataframes_json = [item[1] for item in normalised_dataframes]
            result_dataframes_pandas = [item[0] for item in normalised_dataframes]

            success = True
        except Exception as e:
            print(f"Exception: {str(e)}", file=std_error)

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
            table_metadata = [
                get_table_summary(dataframe) for dataframe in result_dataframes_json
            ]
            metadata = {
                "table_names": dataframe_names,
                "table_metadata": table_metadata,
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
