import json

from shared.apiutils import Router
from analytics_functions import *


router = Router()


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    router.register(variant_frequencies)

    return router.route(event)


if __name__ == "__main__":
    pass
