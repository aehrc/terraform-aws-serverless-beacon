import json

from shared.utils import clear_tmp
from query_engine import perform_query


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    try:
        event = json.loads(event["Records"][0]["Sns"]["Message"])
        is_async = True
        print("using sns event")
    except:
        is_async = False
        print("using invoke event")

    response = perform_query(event, is_async)
    # clear_tmp()
    return response


if __name__ == "__main__":
    e = {
        "query_id": "TEST",
        "dataset_id": "1-0",
        # "samples": ["HG00099"],
        "samples": [],
        "reference_bases": "A",
        "alternate_bases": "N",
        "end_min": 10000001,
        "end_max": 10011011,
        "variant_min_length": 0,
        "variant_max_length": -1,
        "include_details": True,
        "include_samples": True,
        "region": "5:10000001-10001011",
        "vcf_location": "s3://vcf-simulations/fraction-1-vcfs/ALL.chr5.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz",
        "variant_type": None,
        "requested_granularity": "record",
    }
    r = lambda_handler(e, 1)
    print(r)
    pass
