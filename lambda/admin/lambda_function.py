import json

from shared.apiutils import Router
from admin_functions import *


router = Router()


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    router.register(add_user, auth_groups=["admin-group"])
    router.register(get_users, auth_groups=["admin-group"])
    router.register(delete_user, auth_groups=["admin-group"])
    router.register(user_groups, auth_groups=["admin-group"])
    router.register(update_user_groups, auth_groups=["admin-group"])

    return router.route(event)


if __name__ == "__main__":
    pass
