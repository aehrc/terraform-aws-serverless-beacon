import json

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/g_variants":
        return route_g_variants(event)

    elif event['resource'] == '/g_variants/{id}':
        return route_g_variants_id(event)

    elif event['resource'] == '/g_variants/{id}/individuals':
        return route_g_variants_id_individuals(event)

    elif event['resource'] == '/g_variants/{id}/biosamples':
        return route_g_variants_id_biosamples(event)


if __name__ == '__main__':
    pass
