import json

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/g_variants":
        return route_g_variants(event)

    elif event['resource'] == '/g_variants/{id}':
        return route_g_variants_id(event)

    # elif event['resource'] == '/g_variants/{id}/biosamples':
    #     entry = responses.result_sets_response
    #     entry['response']['resultSets'][0]['results'] = [
    #         entries.biosample_entry]
    #     return from script

    elif event['resource'] == '/g_variants/{id}/individuals':
        return route_g_variants_id(event)


if __name__ == '__main__':
    event = {
        "resource": "/g_variants",
        "path": "/g_variants",
        "httpMethod": "POST",
        "body": json.dumps({
            "query": {
                "requestParameters": {
                "assemblyId": "GRCH38",
                "includeResultsetResponses": "HIT",
                "start": [
                    10000000,
                    10001000
                ],
                "end": [
                    10000000,
                    10001000
                ],
                "referenceBases": "A",
                "referenceName": "5",
                "alternateBases": "G"
                },
                "requestedGranularity": "record"
            }
        })
    }

    # event = {
    #     "resource": "/g_variants/{id}",
    #     "path": "/g_variants/{id}",
    #     "httpMethod": "GET",
    #     "pathParameters": {
    #         "id": "R1JDSDM4CTUJMTAwMDA2NTgJQQlH"
    #     },
    #     "queryStringParameters": {
    #         "requestedGranularity": "record"
    #     },
    #     "body": json.dumps({
    #     })
    # }

    print(lambda_handler(event, dict()))