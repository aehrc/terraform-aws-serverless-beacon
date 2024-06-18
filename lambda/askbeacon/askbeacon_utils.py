from functools import cache
from typing import List

import joblib
import numpy as np
from docarray.index import InMemoryExactNNIndex
from models import VecDBEntry, embeddings_model
from shared.apiutils import AuthError
from shared.utils import ENV_ATHENA
from smart_open import open as sopen


def authenticate_endpoint(event, context):
    authorizer = event["requestContext"]["authorizer"]
    groups = authorizer["claims"]["cognito:groups"].split(",")

    if not "record-access-user-group" in groups:
        raise AuthError(
            error_code="Unauthorised",
            error_message="User does not have access",
        )


@cache
def get_vec_db():
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/askbeacon-db/db.pkl.bz2", "rb"
    ) as fo:
        docs = joblib.load(fo)
        db = InMemoryExactNNIndex[VecDBEntry]()
        db.index(docs)

    return db


def search_db(condition: str) -> List[VecDBEntry]:
    embedding = embeddings_model.embed_query(condition)
    embedding = np.array(embedding)

    db = get_vec_db()
    matches, scores = db.find(embedding, search_field="embedding", limit=20)
    return [m for (m, s) in zip(matches, scores) if s > 0.8]
