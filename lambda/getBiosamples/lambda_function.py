import json

from route_biosamples import route as route_biosamples
from route_biosamples_id import route as route_biosamples_id
from route_biosamples_id_g_variants import route as route_biosamples_id_g_variants
from route_biosamples_id_analyses import route as route_biosamples_id_analyses


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/biosamples":
        return route_biosamples(event)

    elif event['resource'] == '/biosamples/{id}':
        return route_biosamples_id(event)

    elif event['resource'] == '/biosamples/{id}/g_variants':
        return route_biosamples_id_g_variants(event)

    elif event['resource'] == '/biosamples/{id}/analyses':
        return route_biosamples_id_analyses(event)

    elif event['resource'] == '/biosamples/{id}/runs':
        return route_biosamples_id_analyses(event)


if __name__ == '__main__':
    pass
