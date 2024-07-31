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


@router.attach("/ask/analytics/prompt_analysis", "post", authenticate_endpoint)
def prompt_analysis(event, _):
    body_dict = json.loads(event.get("body"))
    query = body_dict["query"]
    try:
        code = generate_analysis_code(query)
        return {"success": True, "code": code}
    except Exception as e:
        return {"success": False, "code": f"# Unable to generate code\n# {str(e)}"}


@router.attach("/ask/analytics/execute_analysis", "post", authenticate_endpoint)
def execute_analysis(event, _):
    body_dict = json.loads(event.get("body"))
    code = body_dict["code"]
    result = run_analysis(code)

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


# if __name__ == "__main__":
#     import os
#     from textwrap import dedent

#     url = f"https://{os.environ['SBEACON_API_URL']}/prod"
#     header = f"Bearer {os.environ['SBEACON_TEST_TOKEN']}"

#     code = dedent(
#         """
#         data1 = (
#             BeaconV2()
#             .with_scope('individuals')
#             .with_limit(5)
#             .load()
#         )

#         data2 = (
#             BeaconV2()
#             .with_scope('biosamples')
#             .with_limit(5)
#             .load()
#         )

#         print(json.dumps(data2, indent=4))

#         dataframes = [data1, data2]
#     """
#     )

#     print(code)
#     result = run_extractors(url, header, code)
#     print(result)

# if __name__ == "__main__":
#     query = "Plot the frequency of different karyotypic sex attributes"
#     generate_analysis_code(query)


# if __name__ == "__main__":
#     from pprint import pprint
#     from textwrap import dedent

#     code = dedent(
#         """
#         karyotypic_sex_counts = data_individuals['karyotypicSex'].value_counts()
#         plt.figure(figsize=(10, 6)) # Set the figure size
#         sns.barplot(x=karyotypic_sex_counts.index, y=karyotypic_sex_counts.values) # Create the bar plot using seaborn
#         plt.title('Frequency of Different Karyotypic Sex Attributes') # Set the title of the plot
#         plt.xlabel('Karyotypic Sex') # Set the x-axis label
#         plt.ylabel('Frequency') # Set the y-axis label

#         output_file_path = '/tmp/karyotypic_sex_frequency.png'
#         plt.savefig(output_file_path, dpi=300)

#         output_files = [output_file_path]


#         files = ['/tmp/karyotypic_sex_frequency.png']
#     """
#     )

#     print(code)
#     result = run_analysis(code)
#     pprint(result)
