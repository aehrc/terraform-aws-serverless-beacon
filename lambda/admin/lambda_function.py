import json

from admin_functions import router as admin_router
from shared.apiutils import LambdaRouter

router = LambdaRouter()


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    router.update(admin_router)
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
