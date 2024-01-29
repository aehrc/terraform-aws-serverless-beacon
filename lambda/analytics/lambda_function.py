import json

from shared.apiutils import Router
from variant_frequencies import variant_frequencies


router = Router()


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    router.register(variant_frequencies, auth_groups=['record-access-user-group'])

    return router.route(event)


if __name__ == "__main__":
    pass
