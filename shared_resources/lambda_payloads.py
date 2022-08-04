import jsons


# payload accepted by SplitQuery lambda
class SplitQueryPayload:
    def __init__(self, *, 
            dataset_id,
            reference_bases,
            region_start,
            region_end,
            end_min,
            end_max,
            alternate_bases,
            variant_type,
            include_datasets,
            vcf_locations,
            vcf_groups,
            requested_granularity,
            variant_min_length,
            variant_max_length
        ):
        self.dataset_id = dataset_id
        self.reference_bases = reference_bases
        self.region_start = region_start
        self.region_end = region_end
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


class PerformQueryPayload():
    def __init__(self, *,
            mode='search',
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
            position=None,
            chrom=None
        ):
        self.mode = mode
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
        self.position = position
        self.chrom = chrom
