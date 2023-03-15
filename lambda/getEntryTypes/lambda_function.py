import json


from apiutils.framework import entry_types
from apiutils.responses import bundle_response


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = entry_types()
    print('Returning Response: {}'.format(json.dumps(response)))
    return bundle_response(200, response)
