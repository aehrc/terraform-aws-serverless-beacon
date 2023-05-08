from typing import Dict, List

from shared.athena import Dataset
from shared.dynamodb import Anscestors, Descendants
from shared.ontoutils import get_term_all_descendants, get_term_descendants_in_beacon, get_term_all_ancestors
from shared.utils import ENV_ATHENA


# TODO LRU caching for get_term ancestors
# TODO refetch new ontology term ancestors
def is_duo_restrictions_match(
    dataset: Dataset,
    disease_focussed_research: bool = False,
    method_development: bool = False,
    control_set: bool = False,
    study_pop_origins: bool = False,
    commercial_use: bool = False,
    diseases: List[Dict] = [],
):
    du_conditions: List[Dict] = dataset.dataUseConditions["duoDataUse"]

    no_conditions = [c for c in du_conditions if c["id"] == "DUO:0000004"]
    if no_conditions:
        return True

    # term and its parents for each requested disease
    disease_parents = {
        parent_term
        for term in diseases
        for parent_term in get_term_all_ancestors(term["id"])
    }

    if disease_focussed_research:
        # disease specific research
        gru_flag = len([c for c in du_conditions if c["id"] == "DUO:0000042"]) > 0
        hmb_flag = len([c for c in du_conditions if c["id"] == "DUO:0000006"]) > 0
        dsx_flag = False

        if ds_condition := [c for c in du_conditions if c["id"] == "DUO:0000007"]:
            # all modifier terms must appear in disease_parents
            modifier_terms = [m["id"] for m in ds_condition[0]["modifiers"]]
            dsx_flag = all([term in disease_parents for term in modifier_terms])

        return gru_flag or hmb_flag or dsx_flag

    # TODO - requires validation
    elif method_development:
        NMDS = get_term_all_descendants("DUO:0000017")
        nmds_conditions = [c for c in du_conditions if c["id"] in NMDS]
        dsx_flag = True

        # all modifier terms must appear in disease_parents
        if nmds_conditions:
            for condition in nmds_conditions:
                modifier_terms = [m["id"] for m in condition["modifiers"]]
                dsx_flag = dsx_flag and all(
                    [term in disease_parents for term in modifier_terms]
                )

        return len(nmds_conditions) == 0 or dsx_flag

    elif control_set:
        gru_flag = len([c for c in du_conditions if c["id"] == "DUO:0000042"]) > 0
        hmb_flag = len([c for c in du_conditions if c["id"] == "DUO:0000006"]) > 0
        no_nctrl_flag = len([c for c in du_conditions if c["id"] == "DUO:0000036"]) == 0
        dsx_flag = False

        # research control restrictions must match
        if ds_condition := [c for c in du_conditions if c["id"] == "DUO:0000036"]:
            # all modifier terms must appear in disease_parents
            modifier_terms = [m["id"] for m in ds_condition[0]["modifiers"]]
            dsx_flag = all([term in disease_parents for term in modifier_terms])

        return ((not no_nctrl_flag) and (gru_flag or hmb_flag)) or dsx_flag

    elif study_pop_origins:
        gru_flag = len([c for c in du_conditions if c["id"] == "DUO:0000042"]) > 0
        return gru_flag

    elif commercial_use:
        ncu_npu_flag = (
            len(
                [
                    c
                    for c in du_conditions
                    if c["id"] in get_term_all_descendants("DUO:0000018")
                ]
            )
            == 0
        )
        return ncu_npu_flag

    return False


def filter_datasets(
    datasets: List[Dataset],
    disease_focussed_research: bool = False,
    method_development: bool = False,
    control_set: bool = False,
    study_pop_origins: bool = False,
    target_commercial: bool = False,
    diseases: List[Dict] = [],
):
    return [
        dataset
        for dataset in datasets
        if is_duo_restrictions_match(
            datasets,
            disease_focussed_research,
            method_development,
            control_set,
            study_pop_origins,
            target_commercial,
            diseases,
        )
    ]


if __name__ == "__main__":
    pass
