from route_create_dataset import route as route_create_dataset
from route_update_dataset import route as route_update_dataset


def lambda_handler(event, context):
    if event["resource"] == "/submit_dataset":
        return route_create_dataset(event)

    elif event["resource"] == "/submit_dataset/{id}":
        return route_update_dataset(event, event["pathParameters"].get("id", None))


if __name__ == "__main__":
    pass
