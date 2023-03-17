def get_variant_entry(internal_id, seq_id, ref, alt, start, end, typ):
    return {
        "variantInternalId": internal_id,
        "variation": {
            "referenceBases": ref,
            "alternateBases": alt,
            "location": {
                "interval": {
                    "start": {"type": "Number", "value": start},
                    "end": {"type": "Number", "value": end},
                    "type": "SequenceInterval",
                },
                "sequence_id": seq_id,
                "type": "SequenceLocation",
            },
            "variantType": typ,
        },
    }
