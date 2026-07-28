from typing import List, Union

from shared.apiutils import (
    AlphanumericFilter,
    CustomFilter,
    OntologyFilter,
    Operator,
)
from shared.utils import ENV_ATHENA
from shared.variantutils import perform_variant_search
from shared.apiutils import RequestParams, Granularity

from .genotype import Genotype
from .sample import Sample
from .snp import Snp
from .phenotype import Phenotype

table_request_params = {
    "sample_id": Genotype,
    "value": Genotype,
    "score": Genotype,
    "theta": Genotype,
    "b_allele_freq": Genotype,
    "breed": Sample,
    "sex": Sample,
    "id": Snp,
    "chromosome": Snp,
    "coordinate": Snp,
    "allelea_top_base": Snp,
    "alleleb_top_base": Snp,
    "birth_weight_kg": Phenotype,
    "weaning_weight_kg": Phenotype,
    "six_month_weight_kg": Phenotype,
    "fat_thickness_cm": Phenotype,
    "eye_muscle_area_cm2": Phenotype,
    "height_at_withers_cm": Phenotype,
    "chest_girth_cm": Phenotype,
    "shin_circumference_cm": Phenotype,
    "pre_weaning_gain_kg": Phenotype,
    "post_weaning_gain_kg": Phenotype,
    "daily_weight_gain_kg": Phenotype
}
type_table_id = {
    "genotypes": "sample_id",
    "samples": "sample_id",
    "snps": "id",
    "phenotypes": "sample_id"
}

# # given a dict <f>={"operator":X,"value":Y} return appropriate SQL fragment "<operator> <value>"
# def _get_comparison_operator(filter: Union[AlphanumericFilter, OntologyFilter]):
#     if isinstance(filter.value, int) or isinstance(filter.value, float):
#         # infer a numeric comparison
#         return "!=" if filter.operator == Operator.NOT else filter.operator
#     # infer an alphanumeric comparison
#     return "LIKE" if filter.operator == Operator.EQUAL else "NOT LIKE"

def _get_comparison_operator(filter: Union[AlphanumericFilter, OntologyFilter]):
    if filter.operator == Operator.NOT:
        return "!="

    return filter.operator.value


def entity_search_conditions(
    filters: List[Union[OntologyFilter, AlphanumericFilter, CustomFilter]],
    id_type: str,
    default_scope: str,
    id_modifier="id",
    with_where=True,
    request: RequestParams | None = None,
):
    # arrays to gradually form the SQL expression
    join_constraints = []
    outer_constraints = []
    # using execution parameters to separately pass to boto3 for it to do SQL sanitization
    join_execution_parameters = []
    outer_execution_parameters = []
    filter_samples = []

    # TODO check what the aim of this request is; if it means that we are 100% looking for an individual record
    if request is not None and request.query.request_parameters is not None:
        g_variant = request.query.request_parameters

        print("Performing initial query")
        query_response = perform_variant_search(
            reference_name=g_variant.reference_name,
            reference_bases=g_variant.reference_bases,
            alternate_bases=g_variant.alternate_bases,
            start=g_variant.start,
            end=g_variant.end,
            include_datasets=request.query.include_resultset_responses,
            include_samples=True,
        )


        if query_response:
            sample_names_relevant_to_variant = set()
            sample_names_relevant_to_variant.update(query_response)
            filter_samples = list(sample_names_relevant_to_variant)

            print(f"Found matching samples: {filter_samples}")

            # Everything is joined by the sample id (unique), so we don't need an explicit relations table
            values = ", ".join(["(?)" for _ in filter_samples])

            join_constraints.append(
                f"SELECT sample_id FROM (VALUES {values}) AS t(sample_id)")

            join_execution_parameters += filter_samples
        else:
            # if there are no samples relevant to the variant, then we can return a constraint that will yield no results
            outer_constraints.append("1=0")

    for f in filters:
        if isinstance(f, AlphanumericFilter):
            # check to see if the field is in default scope
            # karyotypicSex = "XX" for default scope (Individuals)
            if f.scope is None or f.scope == default_scope:
                filter_id = f.id.strip().replace(" ", "")

                # naive comparison (JSON will not be in our data)
                operator = _get_comparison_operator(f)
                outer_constraints.append("{} {} ?".format(filter_id, operator))
                outer_execution_parameters.append(str(f.value))
            
            else:
                group = f.scope
                filter_id = f.id.strip().replace(" ", "")

                if group not in type_table_id or filter_id not in table_request_params:
                    continue

                operator = _get_comparison_operator(f)
                comparison = "{} {} ?".format(filter_id, operator)
                join_execution_parameters.append(str(f.value))

                table_id_col = type_table_id[group]
                target_table = table_request_params[filter_id]

                join_constraints.append(
                    f""" SELECT {table_id_col} FROM "{target_table._table_name}" T WHERE {comparison} """
                )

    # format fragments together to form coherent SQL expression
    join_constraints = " INTERSECT ".join(join_constraints)
    join_constraints = (
        f"{type_table_id[id_type]} IN ({join_constraints}) " if join_constraints else ""
    )
    total_constraints = (
        [join_constraints] if join_constraints else []
    ) + outer_constraints
    total_constraints = " AND ".join(total_constraints)
    execution_parameters = join_execution_parameters + outer_execution_parameters

    if total_constraints:
        return (
            ("WHERE " if with_where else "") + total_constraints,
            execution_parameters if execution_parameters else None,
        )
    else:
        return "", None
