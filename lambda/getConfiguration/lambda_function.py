import json

from apiutils.framework import configuration



def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = configuration()
    print('Returning Response: {}'.format(json.dumps(response)))
    return responses.bundle_response(200, response)
