from shared.apiutils import AuthError


def authenticate_admin(event, context):
    authorizer = event["requestContext"]["authorizer"]
    groups = authorizer["claims"]["cognito:groups"].split(",")

    if not "admin-group" in groups:
        raise AuthError(
            error_code="Unauthorised",
            error_message="User does not have admin access",
        )
