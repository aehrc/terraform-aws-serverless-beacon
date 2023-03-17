from dataclasses import dataclass
import jsons

# TODO
# Add comments explaining the variables


# response sent by SplitQuery lambda
@dataclass
class SplitQueryResponse:
    sample: any


# response sent by PerformQuery lambda
@dataclass
class PerformQueryResponse(jsons.JsonSerializable):
    exists: bool
    vcf_location: str
    dataset_id: str
    all_alleles_count: int
    variants: list
    call_count: int
    sample_indices: list
    sample_names: list
