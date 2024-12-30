"""Integrate data from FDA clinical trials API."""

import logging

from regbot.fetch.clinical_trials import StandardAge
from regbot.fetch.clinical_trials import get_clinical_trials as get_trials_from_fda

_logger = logging.getLogger(__name__)


def get_clinical_trials(terms: list[str]) -> dict:
    """Acquire associated clinical trials data for drug term

    >>> from dgipy.dgidb import get_drugs
    >>> from dgipy.integration.clinical_trials import get_clinical_trials
    >>> import polars as pl  # or another dataframe library of your choosing
    >>> drugs = ["imatinib", "sunitinib"]
    >>> df = pl.DataFrame(get_drugs(drugs))
    >>> trial_df = pl.DataFrame(get_clinical_trials(drugs))
    >>> annotated_df = df.join(trial_df, on="drug_name")

    :param terms: drugs of interest
    :return: all clinical trials data for drugs of interest in a DataFrame-ready dict
    """
    if not isinstance(terms, list):
        _logger.warning(
            "Given `terms` arg doesn't appear to be a list. This argument should be a sequence of drug names (as strings)."
        )
    if not terms:
        msg = "Must supply nonempty argument for `terms`"
        raise ValueError(msg)

    output = {
        "drug_name": [],
        "trial_id": [],
        "brief": [],
        "study_type": [],
        "min_age": [],
        "max_age": [],
        "age_groups": [],
        "pediatric": [],
        "conditions": [],
        "interventions": [],
    }

    for drug in terms:
        results = get_trials_from_fda(drug)

        for study in results:
            output["drug_name"].append(drug.upper())
            output["trial_id"].append(study.protocol.identification.nct_id)
            output["brief"].append(study.protocol.identification.brief_title)
            output["study_type"].append(study.protocol.design.study_type)
            min_age = (
                study.protocol.eligibility.min_age
                if study.protocol and study.protocol.eligibility
                else None
            )
            output["min_age"].append(min_age)
            max_age = (
                study.protocol.eligibility.max_age
                if study.protocol and study.protocol.eligibility
                else None
            )
            output["max_age"].append(max_age)
            age_groups = (
                study.protocol.eligibility.std_age
                if study.protocol and study.protocol.eligibility
                else None
            )
            output["age_groups"].append(age_groups)
            output["pediatric"].append(
                StandardAge.CHILD in age_groups if age_groups else None
            )
            output["conditions"].append(
                study.protocol.conditions.conditions
                if study.protocol and study.protocol.conditions
                else None
            )
            output["interventions"].append(
                [i._asdict() for i in study.protocol.arms_intervention.interventions]
                if study.protocol
                and study.protocol.arms_intervention
                and study.protocol.arms_intervention.interventions
                else None
            )
    return output
