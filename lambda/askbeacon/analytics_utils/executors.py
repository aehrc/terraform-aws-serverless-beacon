import contextlib
import io
import json
from copy import copy

import black
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from shared.utils import ENV_ATHENA
from smart_open import open as sopen
from utils.models import GeneratedCodeAnalytics
from utils.s3 import generate_presigned_url
from utils.sanitisers import sanitise
from utils.templates import (
    generate_analytics_table_data,
    get_analytics_code_generator_chain,
)


def generate_analysis_code(job_id: str, query: str) -> str:
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

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/generated_exexutor.py",
        "w",
    ) as fo:
        fo.write(constructed_str)

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/analysis_query.txt",
        "w",
    ) as fo:
        fo.write(query)

    return constructed_str


def run_analysis(job_id: str, code: str):
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

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/executor.py",
        "w",
    ) as fo:
        fo.write(code)

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

    result = {
        "success": success,
        "files": urls,
        "stdout": std_output.getvalue(),
        "stderr": std_error.getvalue(),
    }

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-exec/{job_id}/execution_result.json",
        "w",
    ) as fo:
        json.dump(result, fo)

    return result
