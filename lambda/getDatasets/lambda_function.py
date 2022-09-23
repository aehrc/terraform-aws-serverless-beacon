import json

from route_datasets import route as route_datasets
from route_datasets_id import route as route_datasets_id
from route_datasets_id_g_variants import route as route_datasets_id_g_variants
from route_datasets_id_biosamples import route as route_datasets_id_biosamples
from route_datasets_id_individuals import route as route_datasets_id_individuals
from route_datasets_filtering_terms import route as route_datasets_filtering_terms


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/datasets":
        return route_datasets(event)

    elif event['resource'] == '/datasets/{id}':
        return route_datasets_id(event)

    elif event['resource'] == '/datasets/{id}/g_variants':
        return route_datasets_id_g_variants(event)

    elif event['resource'] == '/datasets/{id}/biosamples':
        return route_datasets_id_biosamples(event)

    elif event['resource'] == '/datasets/{id}/individuals':
        return route_datasets_id_individuals(event)

    elif event['resource'] == '/datasets/filtering_terms':
        return route_datasets_filtering_terms(event)

if __name__ == '__main__':
    pass
