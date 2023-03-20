import jsons


# TODO Add comments explaining the variables
# payload accepted by SplitQuery lambda
class SplitQueryPayload(jsons.JsonSerializable):
    def __init__(
        self,
        *,
        # passthrough variable holds arbitrary data
        # can be used to pass params to splitquery
        passthrough={},
        dataset_id,
        query_id,
        reference_bases,
        start_min,
        start_max,
        end_min,
        end_max,
        alternate_bases,
        variant_type,
        include_datasets,
        vcf_locations,
        vcf_groups,
        requested_granularity,
        variant_min_length,
        variant_max_length,
    ):
        self.passthrough = passthrough
        self.dataset_id = dataset_id
        self.query_id = query_id
        self.reference_bases = reference_bases
        self.start_min = start_min
        self.start_max = start_max
        self.end_min = end_min
        self.end_max = end_max
        self.alternate_bases = alternate_bases
        self.variant_type = variant_type
        self.include_datasets = include_datasets
        self.vcf_locations = vcf_locations
        self.vcf_groups = vcf_groups
        self.requested_granularity = requested_granularity
        self.variant_min_length = variant_min_length
        self.variant_max_length = variant_max_length


class PerformQueryPayload(jsons.JsonSerializable):
    def __init__(
        self,
        *,
        # passthrough variable holds arbitrary data
        passthrough={},
        dataset_id=None,
        query_id="test",
        region=None,
        reference_bases=None,
        end_min=None,
        end_max=None,
        alternate_bases=None,
        variant_type=None,
        include_details=None,
        requested_granularity=None,
        variant_min_length=None,
        variant_max_length=None,
        vcf_location=None,
    ):
        self.passthrough = passthrough
        self.dataset_id = dataset_id
        self.query_id = query_id
        self.region = region
        self.reference_bases = reference_bases
        self.end_min = end_min
        self.end_max = end_max
        self.alternate_bases = alternate_bases
        self.variant_type = variant_type
        self.include_details = include_details
        self.requested_granularity = requested_granularity
        self.variant_min_length = variant_min_length
        self.variant_max_length = variant_max_length
        self.vcf_location = vcf_location
