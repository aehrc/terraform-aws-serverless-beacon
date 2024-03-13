import json

import admin_functions # to initialise router
from shared.apiutils import lambda_router


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    return lambda_router.handle_route(event, context)


if __name__ == "__main__":
    pass
