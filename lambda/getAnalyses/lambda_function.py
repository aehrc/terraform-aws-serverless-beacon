import json

from route_analyses import route as route_analyses
from route_analyses_filtering_terms import route as route_analyses_filtering_terms
from route_analyses_id import route as route_analyses_id
from route_analyses_id_g_variants import route as route_analyses_id_g_variants


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/analyses":
        return route_analyses(event)

    elif event['resource'] == '/analyses/filtering_terms':
        return route_analyses_filtering_terms(event)

    elif event['resource'] == '/analyses/{id}':
        return route_analyses_id(event)

    elif event['resource'] == '/analyses/{id}/g_variants':
        return route_analyses_id_g_variants(event)


if __name__ == '__main__':
    pass
