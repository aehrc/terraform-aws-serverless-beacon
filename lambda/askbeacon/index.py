import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

import joblib
from shared.apiutils.router import LambdaRouter
from shared.dynamodb import TermLabels
from shared.athena import run_custom_query
from shared.utils import ENV_ATHENA
from smart_open import open as sopen
from utils.auth import authenticate_endpoint
from utils.models import VecDBEntry, embeddings_model

router = LambdaRouter()


def parse_athena_result(exec_id: str):
    entries = []
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
    ) as s3f:
        reader = csv.DictReader(s3f)

        for entry in reader:
            entries.append(entry)

    return entries


def get_terms():
    exec_id = run_custom_query(
        f"SELECT * FROM {ENV_ATHENA.ATHENA_TERMS_TABLE}", return_id=True
    )
    athena_entries = [
        entry
        for entry in parse_athena_result(exec_id)
        if len(entry.get("label", "")) > 0
    ]
    dynamo_entries = [
        entry.attribute_values for entry in TermLabels.scan() if len(entry.label) > 0
    ]
    unique_entries = {entry["term"]: entry for entry in athena_entries + dynamo_entries}

    return list(unique_entries.values())


def embed_batch(batch_entries):
    batch_embeddings = embeddings_model.embed_documents(
        [entry["label"] for entry in batch_entries]
    )
    new_entries = []
    for entry, embedding in zip(batch_entries, batch_embeddings):
        new_entry = deepcopy(entry)
        new_entry["embedding"] = embedding
        new_entries.append(new_entry)
    return new_entries


def split_into_chunks(array, chunk_size=50):
    """
    Splits an array into chunks of specified size.

    Parameters:
    array (list): The array to be split.
    chunk_size (int): The size of each chunk. Default is 50.

    Returns:
    list: A list of chunks, where each chunk is a list of up to chunk_size elements from the array.
    """
    # Using list comprehension and slicing to split the array
    return [array[i : i + chunk_size] for i in range(0, len(array), chunk_size)]


@router.attach("/ask/index", "post", authenticate_endpoint)
def index(event, context):
    entries = get_terms()
    batches = split_into_chunks(entries)
    docs = []

    with ThreadPoolExecutor(8) as pool:
        futures = [pool.submit(embed_batch, batch) for batch in batches]
        for future in as_completed(futures):
            entries = future.result()
            for entry in entries:
                docs.append(
                    VecDBEntry(
                        term=entry["term"],
                        label=entry["label"],
                        scope="",
                        embedding=entry["embedding"],
                    )
                )

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-db/db.pkl.bz2", "wb"
    ) as fo:
        joblib.dump(docs, fo, 3)

    return {
        "success": True,
    }


if __name__ == "__main__":
    index("", "")
