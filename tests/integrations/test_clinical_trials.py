import datetime
from pathlib import Path

import requests_mock
from regbot.fetch.clinical_trials import (
    InterventionType,
    StandardAge,
    Status,
    StudyType,
)

from dgipy.integrations.clinical_trials import get_clinical_trials


def test_get_clinical_trials(fixtures_dir: Path):
    with (
        requests_mock.Mocker() as m,
        (
            fixtures_dir / "integration_clinical_trials_zolgensma.json"
        ).open() as json_response,
    ):
        m.get(
            "https://clinicaltrials.gov/api/v2/studies?query.intr=zolgensma",
            text=json_response.read(),
        )
        results = get_clinical_trials(["zolgensma"])
        assert len(results["drug_name"]) == 18
        assert set(results["trial_id"]) == {
            "clinicaltrials:NCT06532474",
            "clinicaltrials:NCT04851873",
            "clinicaltrials:NCT05386680",
            "clinicaltrials:NCT04042025",
            "clinicaltrials:NCT04174157",
            "clinicaltrials:NCT03381729",
            "clinicaltrials:NCT05335876",
            "clinicaltrials:NCT03461289",
            "clinicaltrials:NCT03955679",
            "clinicaltrials:NCT03837184",
            "clinicaltrials:NCT03505099",
            "clinicaltrials:NCT02122952",
            "clinicaltrials:NCT06019637",
            "clinicaltrials:NCT05089656",
            "clinicaltrials:NCT05575011",
            "clinicaltrials:NCT05073133",
            "clinicaltrials:NCT03306277",
            "clinicaltrials:NCT03421977",
        }

        example_index = next(
            i
            for i, trial_id in enumerate(results["trial_id"])
            if trial_id == "clinicaltrials:NCT05386680"
        )
        assert (
            results["brief"][example_index]
            == "Phase IIIb, Open-label, Multi-center Study to Evaluate Safety, Tolerability and Efficacy of OAV101 Administered Intrathecally to Participants With SMA Who Discontinued Treatment With Nusinersen or Risdiplam"
        )
        assert results["study_type"][example_index] == StudyType.INTERVENTIONAL
        assert results["min_age"][example_index] == datetime.timedelta(days=730)
        assert results["age_groups"][example_index] == [StandardAge.CHILD]
        assert results["pediatric"][example_index] is True
        assert results["conditions"][example_index] == ["Spinal Muscular Atrophy"]
        assert results["interventions"][example_index] == [
            {
                "type": InterventionType.GENETIC,
                "name": "OAV101",
                "description": "Intrathecal administration of OAV101 at a dose of 1.2 x 10\\^14 vector genomes, one time dose",
                "aliases": ["AVXS-101", "Zolgensma"],
            }
        ]
        assert (
            results["incl_excl_criteria"][example_index]
            == "Inclusion Criteria\n\n* SMA diagnosis\n* Aged 2 to \\< 18 years\n* Have had at least four loading doses of nusinersen (Spinraza\u00ae) or at least 3 months of treatment with risdiplam (Evrysdi\u00ae) at Screening\n* Must have symptoms of SMA as defined in the protocol\n\nExclusion Criteria:\n\n* Anti Adeno Associated Virus Serotype 9 (AAV9) antibody titer using an immunoassay is reported as elevated\n* Clinically significant abnormalities in test results during screening\n* Contraindications for lumbar puncture procedure\n* At Baseline, participants are excluded if they received:\n\n  * nusinersen (Spinraza\u00ae) or\n  * risdiplam (Evrysdi\u00ae) within a defined timeframe\n* Vaccinations 2 weeks prior to administration of OAV101\n* Hospitalization for a pulmonary event, or for nutritional support within 2 months prior to Screening or inpatient major surgery planned.\n* Presence of an infection or febrile illness up to 30 days prior to administration of OAV101\n* Requiring invasive ventilation"
        )
        assert {
            "name": "Child Hosp of the Kings Daughters",
            "status": Status.RECRUITING,
            "city": "Norfolk",
            "country": "United States",
            "coordinates": (36.84681, -76.28522),
        } in results["potential_sites"][3]
