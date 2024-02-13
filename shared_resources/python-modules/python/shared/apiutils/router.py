import re
from functools import wraps
from collections import defaultdict

from botocore.exceptions import ClientError

from shared.apiutils.responses import bundle_response


class BeaconError(Exception):
    def __init__(self, error_code, error_message):
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(self.error_message)

    def __str__(self):
        return f'Error Code: {self.error_code}, Error Message: "{self.error_message}"'


class AuthError(Exception):
    def __init__(self, error_code, error_message):
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(self.error_message)

    def __str__(self):
        return f'Auth Error: "{self.error_message}"'


def path_pattern_matcher(pattern, method):
    """
    Decorator to match a request path against a template string pattern.
    If the path matches the pattern, the matched variables are added to the function's arguments.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request_path, request_method, auth_groups, event):
            # Convert the pattern into a regular expression
            pattern_regex = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", pattern)
            pattern_regex = f"^{pattern_regex}$"

            match = re.match(pattern_regex, request_path)

            if match and method.lower() == request_method.lower():
                # Check if authorisation is good
                user_groups = event["requestContext"]["authorizer"]["claims"][
                    "cognito:groups"
                ].split(",")
                if not all([auth_group in user_groups for auth_group in auth_groups]):
                    raise AuthError(
                        error_code="Unauthorised",
                        error_message="User does not have access",
                    )
                # Extract matched variables from the request path
                path_vars = match.groupdict()
                return func(event, **path_vars)
            else:
                return None  # No match

        return wrapper

    return decorator


class Router:
    """Router: manages the route functions."""

    # TODO retrieve roles, create a session client to be used by handlers

    def __init__(self):
        # Create the chain of handlers
        self.handlers = []
        # Authorised user groups
        self.auth_groups = defaultdict(list)

    def register(self, handler, auth_groups=[]):
        # register handlers and their groups
        self.handlers.append(handler)
        self.auth_groups[handler] = auth_groups

    def route(self, event):
        http_method = event["httpMethod"]
        request_path = (
            event["pathParameters"].get("proxy", "") if event["pathParameters"] else {}
        )

        for handler in self.handlers:
            try:
                response = handler(
                    request_path, http_method, self.auth_groups[handler], event
                )
            except ClientError as error:
                error_code = error.response["Error"]["Code"]
                error_message = error.response["Error"]["Message"]
                print(f"An error occurred: {error_code} - {error_message}")
                return bundle_response(
                    500, {"error": error_code, "message": error_message}
                )
            except BeaconError as error:
                print(f"An error occurred: {error.error_code} - {error.error_message}")
                return bundle_response(
                    500, {"error": error.error_code, "message": error.error_message}
                )
            except AuthError as error:
                print(f"An error occurred: {error.error_code} - {error.error_message}")
                return bundle_response(
                    401, {"error": error.error_code, "message": error.error_message}
                )
            except Exception as e:
                print(f"An error occurred: {e}")
                return bundle_response(
                    500, {"error": "UnhandledException", "message": str(e)}
                )

            if response:
                return bundle_response(200, response)

        return bundle_response(404, {})
