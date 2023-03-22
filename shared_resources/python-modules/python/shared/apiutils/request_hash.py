import json
import hashlib


def hash_query(event):
    hash_attr = {
        "body",
        "httpMethod",
        "path",
        "pathParameters",
        "queryStringParameters",
    }
    hash_event = {attr: event.get(attr, None) for attr in hash_attr}

    if hash_event.get("body"):
        hash_event["body"] = json.loads(hash_event["body"])
    event_str = json.dumps(hash_event, sort_keys=True)

    return hashlib.md5(event_str.encode()).hexdigest()
