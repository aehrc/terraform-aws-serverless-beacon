import json

from shared.apiutils import LambdaRouter
from variant_correlations import router as v_corr_router
from variant_frequencies import router as v_freq_router

router = LambdaRouter()


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    router.update(v_corr_router)
    router.update(v_freq_router)
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
