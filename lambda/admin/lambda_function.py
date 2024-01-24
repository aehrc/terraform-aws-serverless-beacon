import json

from shared.apiutils import Router
from admin_functions import *


router = Router()


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    router.register(add_user)
    router.register(get_users)
    router.register(delete_user)
    router.register(user_groups)
    router.register(update_user_groups)

    return router.route(event)


if __name__ == "__main__":
    pass
