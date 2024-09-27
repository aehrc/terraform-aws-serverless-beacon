import json
import traceback

from botocore.exceptions import ClientError
from shared.apiutils.responses import DateTimeEncoder, bundle_response


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


class LambdaRouter:
    def __init__(self):
        self._routes = {}

    def attach(self, path, method, auth_func=None):
        """
        A decorator for adding routes.

        :param path: The path to match, with parameters in curly braces, e.g., /users/{userId}
        :param method: HTTP method to match, e.g. get
        :param auth_func: An optional authorization function that takes the event and context.
                          It should raise an exception if authorization fails.
        """

        def decorator(func):
            self._add_route(path, method, func, auth_func)
            return func

        return decorator

    def update(self, router):
        """
        Update the router with another router. Overwrite if the same route is defined in multiple places.

        :param router: Another router object.
        :return: None.
        """
        self._routes.update(router._routes)

    def handle_route(self, event, context):
        """
        Route an incoming request to the appropriate handler.

        :param event: The event dict provided by AWS Lambda proxy integration.
        :param context: The context object provided by AWS Lambda.
        :return: The response from the handler or an error response.
        """
        print("Event Received: {}".format(json.dumps(event)))
        path = event["path"]
        handler = None
        auth_func = None
        route = None

        for _route, _method in self._routes:
            if not (
                _method == event["httpMethod"].lower()
                and self._match_path(_route, path)
            ):
                continue

            handler = self._routes[(_route, _method)]["handler"]
            auth_func = self._routes[(_route, _method)].get("auth")
            route = _route

        if handler is None:
            return bundle_response(404, {})

        try:
            if auth_func:
                auth_func(event, context)

            path_parameters = self._extract_path_parameters(route, path)
            event["pathParameters"] = path_parameters
            response = handler(event, context)
            print("Response Body: {}".format(json.dumps(response, cls=DateTimeEncoder)))

            return bundle_response(200, response)

        except ClientError as error:
            error_code = error.response["Error"]["Code"]
            error_message = error.response["Error"]["Message"]
            print(f"A client error occurred: {error_code} - {error_message}")
            print(traceback.format_exc())
            return bundle_response(500, {"error": error_code, "message": error_message})

        except BeaconError as error:
            print(
                f"A beacon error occurred: {error.error_code} - {error.error_message}"
            )
            print(traceback.format_exc())
            return bundle_response(
                500, {"error": error.error_code, "message": error.error_message}
            )

        except AuthError as error:
            print(f"An auth error occurred: {error.error_code} - {error.error_message}")
            print(traceback.format_exc())
            return bundle_response(
                401, {"error": error.error_code, "message": error.error_message}
            )

        except Exception as e:
            print(f"An unhandled error occurred: {e}")
            print(traceback.format_exc())
            return bundle_response(
                500, {"error": "UnhandledException", "message": str(e)}
            )

    def _add_route(self, path, method, handler, auth_func=None):
        """
        Add a route to the router.

        :param path: The path to match, with parameters in curly braces, e.g., /users/{userId}
        :param method: HTTP method to match, e.g. get
        :param handler: The function to handle the request.
        :param auth_func: An optional authorization function that takes the event and context.
                          It should raise an exception if authorization fails.
        """

        self._routes[(path, method.lower())] = {"handler": handler, "auth": auth_func}

    def _match_path(self, route, path):
        """
        Check if the requested path matches the route.
        """
        route_parts = route.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        if len(route_parts) != len(path_parts):
            return False

        for route_part, path_part in zip(route_parts, path_parts):
            if route_part.startswith("{") and route_part.endswith("}"):
                continue
            if route_part != path_part:
                return False

        return True

    def _extract_path_parameters(self, route, path):
        """
        Extract path parameters based on the route definition.
        """
        params = {}
        route_parts = route.strip("/").split("/")
        path_parts = path.strip("/").split("/")

        for route_part, path_part in zip(route_parts, path_parts):
            if route_part.startswith("{") and route_part.endswith("}"):
                param_name = route_part.strip("{}")
                params[param_name] = path_part

        return params
