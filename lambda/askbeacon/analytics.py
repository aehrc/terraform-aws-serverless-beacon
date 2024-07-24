import json

from analytics_utils import (
    BeaconV2,
    generate_analytics_code,
    generate_extractor_code,
    run_extractors,
)
from shared.apiutils.router import LambdaRouter
from utils.auth import authenticate_endpoint

router = LambdaRouter()


@router.attach("/ask/analytics/prompt_extraction", "post", authenticate_endpoint)
def prompt_extraction(event, _):
    body_dict = json.loads(event.get("body"))
    query = body_dict["query"]
    try:
        code = generate_extractor_code(query)
        return {"success": True, "code": code}
    except Exception as e:
        return {"success": False, "code": f"# Unable to generate code\n# {str(e)}"}


@router.attach("/ask/analytics/execute_extraction", "post", authenticate_endpoint)
def execute_extraction(event, _):
    header = event["headers"]["Authorization"]
    url = f"https://{event['requestContext']['domainName']}/prod"
    body_dict = json.loads(event.get("body"))
    code = body_dict["code"]
    result = run_extractors(url, header, code)

    return {"success": True, **result}


@router.attach("/ask/analytics/test", "post", authenticate_endpoint)
def test(event, _):
    header = event["headers"]["Authorization"]
    url = f"https://{event['requestContext']['domainName']}/prod"

    data = (
        BeaconV2(url, header)
        .with_scope("individuals")
        .with_skip(0)
        .with_limit(5)
        .load()
    )

    return {"success": True, "reponse": data}


if __name__ == "__main__":
    import os
    from pprint import pprint
    from textwrap import dedent

    url = f"https://{os.environ['SBEACON_API_URL']}/prod"
    header = f"Bearer {os.environ['SBEACON_TEST_TOKEN']}"

    code = dedent(
        """
        data1 = (
            BeaconV2()
            .with_scope('individuals')
            .with_limit(5)
            .load()
        )

        data2 = (
            BeaconV2()
            .with_scope('biosamples')
            .with_limit(5)
            .load()
        )

        dataframes = [data1, data2]
    """
    )

    print(code)
    result = run_extractors(url, header, code)
    pprint(result)

# if __name__ == "__main__":
#     query = "Plot the frequency of different karyotypic sex attributes"
#     generate_analytics_code(query)
