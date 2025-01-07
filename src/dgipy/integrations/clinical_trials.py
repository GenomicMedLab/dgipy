"""Integrate data from FDA clinical trials API."""

import logging

from regbot.fetch.clinical_trials import StandardAge, Status, Study
from regbot.fetch.clinical_trials import get_clinical_trials as get_trials_from_fda

_logger = logging.getLogger(__name__)


def _add_study_to_output(output: dict[str, list], drug_name: str, study: Study) -> None:
    """Update `output` in-place with results from study

    :param output: in-progress raw columnar data
    :param drug_name: name of drug that was searched
    :param study: clinical trial study data to add to output
    """
    output["drug_name"].append(drug_name.upper())
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
    output["pediatric"].append(StandardAge.CHILD in age_groups if age_groups else None)
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
    eligibility = study.protocol.eligibility
    if not eligibility:
        output["incl_excl_criteria"].append(None)
        output["population_sex"].append(None)
        output["population_description"]
    else:
        output["incl_excl_criteria"].append(eligibility.description)
        output["population_sex"].append(eligibility.sex)
        output["population_description"].append(eligibility.population)
    all_locations = (
        study.protocol.contacts_locations.locations
        if study.protocol.contacts_locations
        and study.protocol.contacts_locations.locations
        else []
    )

    potential_sites = [
        {
            "name": location.facility,
            "status": location.status,
            "city": location.city,
            "country": location.country,
            "coordinates": location.geo,
        }
        for location in all_locations
        if location.status
        in {
            Status.RECRUITING,
            Status.NOT_YET_RECRUITING,
            Status.AVAILABLE,
            Status.TEMPORARILY_NOT_AVAILABLE,
            Status.UNKNOWN,
        }
    ]
    output["potential_sites"].append(potential_sites)


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
        "incl_excl_criteria": [],
        "population_sex": [],
        "population_description": [],
        "potential_sites": [],
    }

    for drug in terms:
        results = get_trials_from_fda(drug)

        for study in results:
            _add_study_to_output(output, drug, study)

    return output
