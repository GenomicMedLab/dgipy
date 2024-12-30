import datetime
from pathlib import Path

import requests_mock
from regbot.fetch.clinical_trials import InterventionType, StandardAge, StudyType

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
