from shared.apiutils import AuthError
from smart_open import open as sopen


def authenticate_endpoint(event, context):
    authorizer = event["requestContext"]["authorizer"]
    groups = authorizer["claims"]["cognito:groups"].split(",")

    if not "record-access-user-group" in groups:
        raise AuthError(
            error_code="Unauthorised",
            error_message="User does not have access",
        )
