from typing import List, Union

from shared.apiutils import (
    AlphanumericFilter,
    CustomFilter,
    OntologyFilter,
    Operator,
    Similarity,
)
from shared.ontoutils import (
    get_term_ancestors_in_beacon,
    get_term_descendants_in_beacon,
)
from shared.utils import ENV_ATHENA
from shared.variantutils import perform_variant_search
from shared.apiutils import RequestParams, Granularity

from .analysis import Analysis
from .biosample import Biosample
from .cohort import Cohort
from .dataset import Dataset, get_datasets
from .individual import Individual
from .run import Run

type_class = {
    "individuals": Individual,
    "biosamples": Biosample,
    "runs": Run,
    "analyses": Analysis,
    "datasets": Dataset,
    "cohorts": Cohort,
}
type_relations_table_id = {
    "individuals": "individualid",
    "biosamples": "biosampleid",
    "runs": "runid",
    "analyses": "analysisid",
    "datasets": "datasetid",
    "cohorts": "cohortid",
}


# given a dict <f>={"operator":X,"value":Y} return appropriate SQL fragment "<operator> <value>"
def _get_comparison_operator(filter: Union[AlphanumericFilter, OntologyFilter]):
    if isinstance(filter.value, int) or isinstance(filter.value, float):
        # infer a numeric comparison
        return "!=" if filter.operator == Operator.NOT else filter.operator
    # infer an alphanumeric comparison
    return "LIKE" if filter.operator == Operator.EQUAL else "NOT LIKE"


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

    if request is not None and request.query.request_parameters is not None:
        g_variant = request.query.request_parameters
        datasets = get_datasets(g_variant.assembly_id, skip=0, limit="ALL")

        query_responses = perform_variant_search(
            datasets=datasets,
            reference_name=g_variant.reference_name,
            reference_bases=g_variant.reference_bases,
            alternate_bases=g_variant.alternate_bases,
            start=g_variant.start,
            end=g_variant.end,
            variant_type=g_variant.variant_type,
            variant_min_length=g_variant.variant_min_length,
            variant_max_length=g_variant.variant_max_length,
            requested_granularity=Granularity.RECORD,
            include_datasets=request.query.include_resultset_responses,
            dataset_samples=[],
            include_samples=True,
        )

        sample_names_relevant_to_variant = set()
        for query_response in query_responses:
            sample_names_relevant_to_variant.update(query_response.sample_names)

        filter_samples = list(sample_names_relevant_to_variant)

        if filter_samples:
            join_constraints.append(
                f""" SELECT RI.{type_relations_table_id[id_type]} FROM "{ENV_ATHENA.ATHENA_RELATIONS_TABLE}" RI JOIN "{Analysis._table_name}" S ON RI.analysisid=S.id WHERE S._vcfsampleid IN ({', '.join(['?' for s in filter_samples])}) """
            )
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

                if "." not in filter_id:
                    # naive comparison
                    operator = _get_comparison_operator(f)
                    outer_constraints.append("{} {} ?".format(filter_id, operator))
                    outer_execution_parameters.append(f"'{str(f.value)}'")
                else:
                    # this is a json path comparison
                    json_root = filter_id.split(".", 1)[0]
                    json_path = filter_id.split(".", 1)[1]
                    func_call = f"""comparejsonpath({json_root}, '$.{json_path}', '{f.operator}', ?)"""
                    outer_constraints.append(func_call)
                    outer_execution_parameters.append(f"'{str(f.value)}'")
            # otherwise, we have to use the relations table
            # eg: scope = "cohorts", cohortType = "beacon-defined"
            else:
                group = f.scope
                joined_class = type_class[group]
                filter_id = f.id.strip().replace(" ", "")

                if "." not in filter_id:
                    # naive comparison
                    operator = _get_comparison_operator(f)
                    comparison = "{} {} ?".format(filter_id, operator)
                    join_execution_parameters.append(f"'{str(f.value)}'")
                    join_constraints.append(
                        f""" SELECT RI.{type_relations_table_id[id_type]} FROM "{ENV_ATHENA.ATHENA_RELATIONS_TABLE}" RI JOIN "{joined_class._table_name}" TN ON RI.{type_relations_table_id[group]}=TN.id WHERE TN.{comparison} """
                    )
                else:
                    # this is a json path comparison from a different entity
                    json_root = filter_id.split(".", 1)[0]
                    json_path = filter_id.split(".", 1)[1]
                    func_call = f"""comparejsonpath(TN.{json_root}, '$.{json_path}', '{f.operator}', ?)"""
                    join_execution_parameters.append(f"'{str(f.value)}'")
                    join_constraints.append(
                        f""" SELECT RI.{type_relations_table_id[id_type]} FROM "{ENV_ATHENA.ATHENA_RELATIONS_TABLE}" RI JOIN "{joined_class._table_name}" TN ON RI.{type_relations_table_id[group]}=TN.id WHERE {func_call} """
                    )

        elif isinstance(f, OntologyFilter):
            # by default expanded terms is just the term itself
            expanded_terms = {f.id}
            # if descendantTerms is false, then similarity measures dont really make sense...
            if f.include_descendant_terms:
                # process inclusion of term descendants dependant on 'similarity'
                if f.similarity in (Similarity.HIGH, Similarity.EXACT):
                    expanded_terms = get_term_descendants_in_beacon(f.id)
                else:
                    # NOTE: this simplistic similarity method not nessisarily efficient or nessisarily desirable
                    ancestors = get_term_ancestors_in_beacon(f.id)
                    ancestor_descendants = sorted(
                        [get_term_descendants_in_beacon(a) for a in ancestors], key=len
                    )
                    if f.similarity == Similarity.MEDIUM:
                        # all terms which have an ancestor half way up
                        expanded_terms = ancestor_descendants[
                            len(ancestor_descendants) // 2
                        ]
                    elif f.similarity == Similarity.LOW:
                        # all terms which have any ancestor in common
                        expanded_terms = ancestor_descendants[-1]

            join_execution_parameters += [str(a) for a in expanded_terms]
            expanded_terms = " , ".join(["?" for a in expanded_terms])
            # process scope clarification if specified different
            group = f.scope or default_scope
            join_constraints.append(
                f""" SELECT RI.{type_relations_table_id[id_type]} FROM "{ENV_ATHENA.ATHENA_RELATIONS_TABLE}" RI JOIN "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI ON RI.{type_relations_table_id[group]}=TI.id WHERE TI.kind='{group}' AND TI.term IN ({expanded_terms}) """
            )
        elif isinstance(f, CustomFilter):
            # TODO this is a dummy replacement, for future implementation
            group = f.scope or default_scope
            expanded_terms = "?"
            join_execution_parameters += [f.id]
            join_constraints.append(
                f""" SELECT RI.{type_relations_table_id[id_type]} FROM "{ENV_ATHENA.ATHENA_RELATIONS_TABLE}" RI JOIN "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI ON RI.{type_relations_table_id[group]}=TI.id WHERE TI.kind='{group}' AND TI.term IN ({expanded_terms}) """
            )

    # format fragments together to form coherent SQL expression
    join_constraints = " INTERSECT ".join(join_constraints)
    join_constraints = (
        f"{id_modifier} IN ({join_constraints}) " if join_constraints else ""
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
