from strenum import StrEnum


class VariantEffect(StrEnum):
    MISSENSE_VARIANT = "missense_variant"
    SPLICE_REGION_VARIANT = "splice_region_variant"
    NON_CODING_TRANSCRIPT_EXON_VARIANT = "non_coding_transcript_exon_variant"
