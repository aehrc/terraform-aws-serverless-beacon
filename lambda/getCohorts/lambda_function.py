import json

from route_cohorts import route as route_cohorts
from route_cohorts_id import route as route_cohorts_id
from route_cohorts_id_individuals import route as route_cohorts_id_individuals
from route_cohorts_id_filtering_terms import route as route_cohorts_id_filtering_terms


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event["resource"] == "/cohorts":
        return route_cohorts(event)

    elif event['resource'] == '/cohorts/{id}':
        return route_cohorts_id(event)

    elif event['resource'] == '/cohorts/{id}/individuals':
        return route_cohorts_id_individuals(event)

    elif event['resource'] == '/cohorts/{id}/filtering_terms':
        return route_cohorts_id_filtering_terms(event)


if __name__ == '__main__':
    pass
