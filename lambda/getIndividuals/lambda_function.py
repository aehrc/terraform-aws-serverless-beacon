import json

from route_individuals import route as route_individuals
from route_individuals_filtering_terms import route as route_individuals_filtering_terms
from route_individuals_id import route as route_individuals_id
from route_individuals_id_g_variants import route as route_individuals_id_g_variants
from route_individuals_id_biosamples import route as route_individuals_id_biosamples


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/individuals":
        return route_individuals(event)

    elif event['resource'] == '/individuals/filtering_terms':
        return route_individuals_filtering_terms(event)

    elif event['resource'] == '/individuals/{id}':
        return route_individuals_id(event)

    elif event['resource'] == '/individuals/{id}/g_variants':
        return route_individuals_id_g_variants(event)

    elif event['resource'] == '/individuals/{id}/biosamples':
        return route_individuals_id_biosamples(event)


if __name__ == '__main__':
    pass