import os
from functools import cache
from typing import List

import joblib
import numpy as np
from docarray.index import InMemoryExactNNIndex
from shared.utils import ENV_ATHENA
from smart_open import open as sopen
from utils.models import VecDBEntry, embeddings_model


@cache
def get_vec_db():
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-db/db.pkl.bz2", "rb"
    ) as fp:
        docs = joblib.load(fp)
        db = InMemoryExactNNIndex[VecDBEntry]()
        db.index(docs)

    return db


def search_db(condition: str) -> List[VecDBEntry]:
    embedding = embeddings_model.embed_query(condition)
    embedding = np.array(embedding)
    thresh = float(os.environ["EMBEDDING_DISTANCE_THRESHOLD"])

    db = get_vec_db()
    matches, scores = db.find(embedding, search_field="embedding", limit=3)
    print(f"Search results for: {condition}")
    print(f"\tmatches: {[f"{m.term}:{m.label}" for m in matches]}")
    print(f"\tscores: {[s for s in scores]}")
    return [(m, s) for (m, s) in zip(matches, scores) if s > thresh]
