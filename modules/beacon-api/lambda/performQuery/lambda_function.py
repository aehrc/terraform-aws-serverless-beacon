import json


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
