import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

import joblib
from askbeacon_utils import authenticate_endpoint
from docarray import BaseDoc
from docarray.index import InMemoryExactNNIndex
from docarray.typing import NdArray
from models import VecDBEntry, embeddings_model
from shared.apiutils.router import LambdaRouter
from shared.athena import run_custom_query
from shared.utils import ENV_ATHENA
from smart_open import open as sopen

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
    entries = parse_athena_result(exec_id)
    for entry in entries:
        if len(entry.get("label", "")) == 0:
            continue
    return entries


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
def index():
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
                        scope=entry["kind"],
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
    index()
