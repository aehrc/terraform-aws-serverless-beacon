import json

from shared.utils import clear_tmp
from query_engine import perform_query


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    try:
        event = json.loads(event["Records"][0]["Sns"]["Message"])
        is_async = True
        print("using sns event")
    except:
        is_async = False
        print("using invoke event")

    response = perform_query(event, is_async)
    clear_tmp()
    return response


if __name__ == "__main__":
    pass
