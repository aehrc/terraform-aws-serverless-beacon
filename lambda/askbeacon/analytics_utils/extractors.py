import contextlib
import io
import json
from copy import copy
from typing import Dict, List

import black
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from shared.utils import ENV_ATHENA
from smart_open import open as sopen
from utils.db import search_db
from utils.models import GeneratedCodeAnalytics, Scope, ScopeEnum
from utils.s3 import generate_presigned_url
from utils.sanitisers import sanitise
from utils.templates import (
    generate_analytics_table_data,
    get_analytics_code_generator_chain,
    get_data_extractor_map_chain,
)

from .beacon_sdk import BeaconV2 as _BeaconV2
from .beacon_sdk import normalise_response

job_id = "test"


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


def generate_extractor_code(query: str) -> Dict:
    extractor_chain = get_data_extractor_map_chain()
    extracted_data = extractor_chain.invoke(query)

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
    sdk_construct = "data = BeaconV2()"
    sdk_comments = ""

    scope = extracted_data.get("scope", Scope(scope=ScopeEnum.UNKNOWN))
    filters = extracted_data["filters"]

    if scope.scope != ScopeEnum.UNKNOWN:
        scope = scope.model_dump(mode="json")["scope"]
        sdk_construct += f""".with_scope("{scope}")"""
        sdk_comments += f"""# Scope detected to be '{scope}'.\n"""
    else:
        sdk_comments += f"""# Could not decide a scope for your query.\n"""
        sdk_construct += f""".with_scope('<ENTER YOUR SCOPE>')"""

    for fil in filters:
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

    return sdk_construct


def run_extractors(
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

    return {
        "dataframes": result_dataframes_json,
        "success": success,
        "stdout": std_output.getvalue(),
        "stderr": std_error.getvalue(),
    }


def generate_analysis_code(query):
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/metadata.json",
        "r",
    ) as fp:
        metadata = json.load(fp)

    analytics_code_chain = get_analytics_code_generator_chain()
    data = generate_analytics_table_data(
        metadata["table_names"], metadata["table_metadata"]
    )

    result: GeneratedCodeAnalytics = analytics_code_chain.invoke(
        {"query": query, "data": data}
    )

    constructed_str = f"{result.code}\n\n# Following files are saved\n"
    constructed_str += f"files = {str(result.files)}"
    constructed_str += f"\n\n# Assumptions\n"

    if result.assumptions:
        for a in result.assumptions:
            constructed_str += f"#     {a}\n"
    else:
        constructed_str += f"#     None made\n"

    constructed_str += f"\n# Feedback\n"

    if result.feedback:
        for a in result.feedback:
            constructed_str += f"#     {a}\n"
    else:
        constructed_str += f"#     None given\n"

    return constructed_str


def run_analysis(code):
    std_output = io.StringIO()
    std_error = io.StringIO()
    success = False
    computed_files = []
    exec_globals = copy(globals())

    # load job realted files
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/metadata.json",
    ) as fp:

        metadata = json.load(fp)
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/extracted.pkl.bz2",
        "rb",
    ) as fo:
        dataframes = joblib.load(fo)

    exec_globals["np"] = np
    exec_globals["plt"] = plt
    exec_globals["pd"] = pd
    exec_globals["sns"] = sns
    exec_globals["os"] = None
    exec_globals["sys"] = None

    for name, dataframe in zip(metadata["table_names"], dataframes):
        exec_globals[name] = dataframe

    # We must not use any overlapping variable names
    # variables in the global scpope (above) will not be overwritten
    # if we do that; which means they will remain empty even after edits
    # to reproduce try declaring an empty array dataframes = []
    # this breaks the whole thing
    with contextlib.redirect_stdout(std_output), contextlib.redirect_stderr(std_error):
        try:
            code = sanitise(code)
            exec(code, exec_globals, locals())
            computed_files = locals().get("files", None)

            if not isinstance(computed_files, list):
                raise ValueError(
                    "The variable 'files' was not defined or was not a list!"
                )

            print("Computed files: ", computed_files)

            success = True
        except Exception as e:
            print(f"Exception: {str(e)}", file=std_error)

    urls = []

    if isinstance(computed_files, list):
        for file in computed_files:
            name = file.split("/")[-1]
            with sopen(
                f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/outputs/{name}",
                "wb",
            ) as fo, open(file, "rb") as fp:
                fo.write(fp.read())

            url = generate_presigned_url(
                ENV_ATHENA.ATHENA_METADATA_BUCKET,
                f"askbeacon-exec/{job_id}/outputs/{name}",
            )
            urls.append(url)

    return {
        "success": success,
        "files": urls,
        "stdout": std_output.getvalue(),
        "stderr": std_error.getvalue(),
    }
