import json
import jsons
import re
import os
import glob

import search_variants
import search_variants_in_samples
from payloads.lambda_payloads import PerformQueryPayload

BASES = [
    "A",
    "C",
    "G",
    "T",
    "N",
]

all_count_pattern = re.compile("[0-9]+")
get_all_calls = all_count_pattern.findall


def lambda_handler(event, context):
    files = glob.glob("/tmp/*")
    for file in files:
        try:
            os.unlink(file)
        except OSError as e:
            print(f"Error: {file} - {e.strerror}")

    print("Event Received: {}".format(json.dumps(event)))
    is_async = False
    try:
        event = json.loads(event["Records"][0]["Sns"]["Message"])
        is_async = True
        print("using sns event")
    except:
        is_async = False
        print("using invoke event")

    performQueryPayload = jsons.load(event, PerformQueryPayload)
    # switch operations
    if performQueryPayload.passthrough.get("selectedSamplesOnly", False):
        response = search_variants_in_samples.perform_query(
            performQueryPayload, is_async
        )
    else:
        response = search_variants.perform_query(performQueryPayload, is_async)

    print(f"Returning response")
    return response.dump()


if __name__ == "__main__":
    pass
