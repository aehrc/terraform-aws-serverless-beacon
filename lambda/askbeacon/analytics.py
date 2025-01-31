import json

from analytics_utils import (
    BeaconV2,
    generate_analysis_code,
    generate_extractor_code,
    run_analysis,
    run_extractors,
)
from shared.apiutils.router import LambdaRouter
from utils.auth import authenticate_endpoint

router = LambdaRouter()


@router.attach("/ask/analytics/prompt_extraction", "post", authenticate_endpoint)
def prompt_extraction(event, _):
    body_dict = json.loads(event.get("body"))
    query = body_dict["query"]
    job_id = body_dict["jobId"]

    try:
        code = generate_extractor_code(job_id, query)
        return {"success": True, "code": code}
    except Exception as e:
        return {"success": False, "code": f"# Unable to generate code\n# {str(e)}"}


@router.attach("/ask/analytics/execute_extraction", "post", authenticate_endpoint)
def execute_extraction(event, _):
    header = event["headers"]["Authorization"]
    url = f"https://{event['requestContext']['domainName']}/prod"
    body_dict = json.loads(event.get("body"))
    code = body_dict["code"]
    job_id = body_dict["jobId"]

    result = run_extractors(job_id, url, header, code)

    return {"success": True, **result}


@router.attach("/ask/analytics/prompt_analysis", "post", authenticate_endpoint)
def prompt_analysis(event, _):
    body_dict = json.loads(event.get("body"))
    query = body_dict["query"]
    job_id = body_dict["jobId"]

    try:
        code = generate_analysis_code(job_id, query)
        return {"success": True, "code": code}
    except Exception as e:
        return {"success": False, "code": f"# Unable to generate code\n# {str(e)}"}


@router.attach("/ask/analytics/execute_analysis", "post", authenticate_endpoint)
def execute_analysis(event, _):
    body_dict = json.loads(event.get("body"))
    code = body_dict["code"]
    job_id = body_dict["jobId"]

    result = run_analysis(job_id, code)

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
