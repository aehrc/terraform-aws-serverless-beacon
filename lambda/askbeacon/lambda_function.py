from analytics import router as analytics_router
from ask import router as ask_router
from index import router as index_router
from shared.apiutils import LambdaRouter
from utils.auth import authenticate_endpoint
from utils.models import llm_text

router = LambdaRouter()
router.update(ask_router)
router.update(index_router)
router.update(analytics_router)


@router.attach("/ask/hello", "get", authenticate_endpoint)
def test(event, context):
    try:
        res = llm_text.invoke("Hello")
        return {"success": True, "response_text": res.content}
    except Exception as e:
        return {"success": False, "error": e}


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    event = {
        "path": "/ask/hello",
        "httpMethod": "GET",
        "pathParameters": {"proxy": "hello"},
        "requestContext": {
            "resourceId": "kt5tc3",
            "authorizer": {
                "claims": {
                    "custom:terraform": "true",
                    "sub": "5b8a9ffb-893a-4b50-a2c0-320995868894",
                    "cognito:groups": "admin-group,count-access-user-group,boolean-access-user-group,record-access-user-group",
                    "email_verified": "true",
                    "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_JgrEfkLvx",
                    "cognito:username": "admin@gmail.com",
                    "given_name": "Admin",
                    "origin_jti": "6c621264-67bf-490a-ab72-c8f425c5426b",
                    "cognito:roles": "arn:aws:iam::361439923243:role/admin-group-role",
                    "aud": "2v2a0jk4o3v26t5l1clm07n7um",
                    "event_id": "1361a11e-2e98-40ff-883b-aaec7744701b",
                    "token_use": "id",
                    "auth_time": "1717051129",
                    "exp": "Thu May 30 07:38:49 UTC 2024",
                    "iat": "Thu May 30 06:38:49 UTC 2024",
                    "family_name": "Admin",
                    "jti": "94c74421-863a-4de4-ab8f-9c1cc5588faa",
                    "email": "admin@gmail.com",
                }
            },
        },
        "body": None,
    }
    lambda_handler(event, "context")
