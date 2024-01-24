import datetime
import json
from typing import Optional
import functools

from .requests import RequestParams, Granularity
from .schemas import DefaultSchemas
from shared.utils import ENV_BEACON


HEADERS = {"Access-Control-Allow-Origin": "*"}


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)


#
# Start Thirdparty Code as annotated
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
# CHANGE: variables taken from terraform
#


# Thirdparty code
def build_meta(
    qparams: RequestParams,
    entity_schema: Optional[DefaultSchemas],
    returned_granularity: Granularity,
):
    """ "Builds the `meta` part of the response

    We assume that receivedRequest is the evaluated request (qparams) sent by the user.
    """
    meta = {
        "beaconId": ENV_BEACON.BEACON_ID,
        "apiVersion": ENV_BEACON.BEACON_API_VERSION,
        "returnedGranularity": returned_granularity,
        "receivedRequestSummary": qparams.summary(),
        "returnedSchemas": [entity_schema.value] if entity_schema is not None else [],
    }
    return meta


# Thirdparty code
def build_response_summary(exists, num_total_results):
    if num_total_results is None:
        return {"exists": exists}
    else:
        return {"exists": exists, "numTotalResults": num_total_results}


# Thirdparty code
def build_response(data, num_total_results, qparams, func):
    """ "Fills the `response` part with the correct format in `results`"""

    response = {
        "id": "",  # TODO: Set the name of the dataset/cohort
        "setType": "",  # TODO: Set the type of collection
        "exists": num_total_results > 0,
        "resultsCount": len(data),
        "results": data,
        # 'info': None,
        "resultsHandover": None,  # build_results_handover
    }

    return response


########################################
# Resultset Response
########################################
# Thirdparty code
def build_beacon_resultset_response(
    data,
    num_total_results,
    qparams: RequestParams,
    func_response_type,
    entity_schema: DefaultSchemas,
):
    """ "
    Transform data into the Beacon response format.
    """

    beacon_response = {
        "meta": build_meta(qparams, entity_schema, Granularity.RECORD),
        "responseSummary": build_response_summary(
            num_total_results > 0, num_total_results
        ),
        # TODO: 'extendedInfo': build_extended_info(),
        "response": {
            "resultSets": [
                build_response(data, num_total_results, qparams, func_response_type)
            ]
        },
        # CHANGE: variables taken from terraform
        "beaconHandovers": json.loads(ENV_BEACON.BEACON_HANDOVERS),
    }
    return beacon_response


########################################
# Count Response
########################################
# Thirdparty code
def build_beacon_count_response(
    data,
    num_total_results,
    qparams: RequestParams,
    func_response_type,
    entity_schema: DefaultSchemas,
):
    """ "
    Transform data into the Beacon response format.
    """

    beacon_response = {
        "meta": build_meta(qparams, entity_schema, Granularity.COUNT),
        "responseSummary": build_response_summary(
            num_total_results > 0, num_total_results
        ),
        # TODO: 'extendedInfo': build_extended_info(),
        # CHANGE: variables taken from terraform
        "beaconHandovers": json.loads(ENV_BEACON.BEACON_HANDOVERS),
    }
    return beacon_response


########################################
# Boolean Response
########################################
# Thirdparty code
def build_beacon_boolean_response(
    data,
    num_total_results,
    qparams: RequestParams,
    func_response_type,
    entity_schema: DefaultSchemas,
):
    """ "
    Transform data into the Beacon response format.
    """

    beacon_response = {
        "meta": build_meta(qparams, entity_schema, Granularity.BOOLEAN),
        "responseSummary": build_response_summary(num_total_results > 0, None),
        # TODO: 'extendedInfo': build_extended_info(),
        # CHANGE: variables taken from terraform
        "beaconHandovers": json.loads(ENV_BEACON.BEACON_HANDOVERS),
    }
    return beacon_response


########################################
# Collection Response
########################################
# Thirdparty code
def build_beacon_collection_response(
    data,
    num_total_results,
    qparams: RequestParams,
    func_response_type,
    entity_schema: DefaultSchemas,
):
    beacon_response = {
        "meta": build_meta(qparams, entity_schema, Granularity.RECORD),
        "responseSummary": build_response_summary(
            num_total_results > 0, num_total_results
        ),
        # TODO: 'info': build_extended_info(),
        "beaconHandovers": json.loads(ENV_BEACON.BEACON_HANDOVERS),
        "response": {"collections": func_response_type(data, qparams)},
    }
    return beacon_response


########################################
# Info Response
########################################
# Thirdparty code


def build_beacon_info_response(authorised_datasets, qparams):
    # CHANGE: variables taken from terraform
    beacon_response = {
        "meta": build_meta(qparams, None, Granularity.RECORD),
        "response": {
            "id": ENV_BEACON.BEACON_ID,
            "name": ENV_BEACON.BEACON_NAME,
            "apiVersion": ENV_BEACON.BEACON_API_VERSION,
            "environment": ENV_BEACON.BEACON_ENVIRONMENT,
            "organization": {
                "id": ENV_BEACON.BEACON_ORG_ID,
                "name": ENV_BEACON.BEACON_ORG_NAME,
                "description": ENV_BEACON.BEACON_ORG_DESCRIPTION,
                "address": ENV_BEACON.BEACON_ORG_ADDRESS,
                "welcomeUrl": ENV_BEACON.BEACON_ORG_WELCOME_URL,
                "contactUrl": ENV_BEACON.BEACON_ORG_CONTACT_URL,
                "logoUrl": ENV_BEACON.BEACON_ORG_LOGO_URL,
            },
            "description": ENV_BEACON.BEACON_DESCRIPTION,
            "version": ENV_BEACON.BEACON_VERSION,
            "welcomeUrl": ENV_BEACON.BEACON_WELCOME_URL,
            "alternativeUrl": ENV_BEACON.BEACON_ALTERNATIVE_URL,
            "createDateTime": ENV_BEACON.BEACON_CREATE_DATETIME,
            "updateDateTime": ENV_BEACON.BEACON_UPDATE_DATETIME,
            "datasets": authorised_datasets,
        },
    }

    return beacon_response


########################################
# Service Info Response
########################################
# Thirdparty code
@functools.lru_cache()
def build_beacon_service_info_response():
    # CHANGE: variables taken from terraform
    beacon_response = {
        "id": ENV_BEACON.BEACON_ID,
        "name": ENV_BEACON.BEACON_NAME,
        "type": {
            "group": ENV_BEACON.BEACON_SERVICE_TYPE_GROUP,
            "artifact": ENV_BEACON.BEACON_SERVICE_TYPE_ARTIFACT,
            "version": ENV_BEACON.BEACON_SERVICE_TYPE_VERSION,
        },
        "description": ENV_BEACON.BEACON_DESCRIPTION,
        "organization": {
            "name": ENV_BEACON.BEACON_ORG_NAME,
            "url": ENV_BEACON.BEACON_WELCOME_URL,
        },
        "contactUrl": ENV_BEACON.BEACON_ORG_CONTACT_URL,
        "documentationUrl": ENV_BEACON.BEACON_DOCUMENTATION_URL,
        "createdAt": ENV_BEACON.BEACON_CREATE_DATETIME,
        "updatedAt": ENV_BEACON.BEACON_UPDATE_DATETIME,
        "environment": ENV_BEACON.BEACON_ENVIRONMENT,
        "version": ENV_BEACON.BEACON_VERSION,
    }

    return beacon_response


########################################
# Filtering terms Response
########################################
# Thirdparty code
def build_filtering_terms_response(filtering_terms, resources, qparams: RequestParams):
    return {
        "meta": build_meta(qparams, None, Granularity.RECORD),
        "response": {"resources": resources, "filteringTerms": filtering_terms},
    }


def build_bad_request(*, code, message, qparams: RequestParams):
    return {
        "error": {"errorCode": code, "errorMessage": f"{message}"},
        "meta": build_meta(qparams, None, []),
    }


def bundle_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(body, cls=DateTimeEncoder),
    }
