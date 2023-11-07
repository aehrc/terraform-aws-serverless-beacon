import re
from functools import wraps

from shared.apiutils.responses import bundle_response


def path_pattern_matcher(pattern, method):
    """
    Decorator to match a request path against a template string pattern.
    If the path matches the pattern, the matched variables are added to the function's arguments.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request_path, request_method, *args, **kwargs):
            # Convert the pattern into a regular expression
            pattern_regex = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", pattern)
            pattern_regex = f"^{pattern_regex}$"

            match = re.match(pattern_regex, request_path)

            if match and method.lower() == request_method.lower():
                # Extract matched variables from the request path
                path_vars = match.groupdict()
                return func(*args, **path_vars, **kwargs)
            else:
                return None  # No match

        return wrapper

    return decorator


class Router:
    """Router: manages the route functions."""

    def __init__(self):
        # Create the chain of handlers
        self.handlers = []

    def register(self, handler):
        self.handlers.append(handler)

    def route(self, event):
        try:
            authorized = "admin-group" in event["requestContext"]["authorizer"][
                "claims"
            ]["cognito:groups"].split(",")
            if not authorized:
                return bundle_response(
                    400, {"unauthorized_access": "User does not belong to admin-group"}
                )
        except:
            return bundle_response(
                400, {"unauthorized_access": "User does not belong to admin-group"}
            )
        http_method = event["httpMethod"]
        request_path = (
            event["pathParameters"].get("proxy", "") if event["pathParameters"] else {}
        )

        for handler in self.handlers:
            try:
                response = handler(request_path, http_method, event)
            except Exception as e:
                return bundle_response(500, {"error": str(e)})

            if response:
                return bundle_response(200, response)

        return bundle_response(404, {})
