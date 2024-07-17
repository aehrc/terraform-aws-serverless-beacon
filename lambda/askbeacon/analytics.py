from analytics_utils.extractors import test
from shared.apiutils.router import LambdaRouter
from utils.auth import authenticate_endpoint

router = LambdaRouter()


@router.attach("/ask/analytics", "post", authenticate_endpoint)
def perform_analytics(event, context):
    test()
    return {"success": True}
