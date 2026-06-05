from unittest.mock import patch

from app.utils.program_loader import load_all_accredited_programs


@patch("app.utils.program_aggregator.get_aggregated_programs")
def test_load_all_accredited_programs_uses_aggregator(mock_get_aggregated):
    mock_get_aggregated.return_value = [
        {
            "id": "program-1",
            "university_name": "Example University",
            "program_type": "Clinical Ph.D.",
            "accreditation_sources": ["APA", "PCSAS"],
            "address": "123 Main St, City, ST 12345",
            "website": "https://example.edu/psychology",
            "website_source": "pcsas",
            "accreditation_status": "Accredited",
            "student_outcomes_link": "https://example.edu/outcomes.pdf",
            "next_site_visit_year": 2028,
            "openalex_institution_id": "https://openalex.org/I123",
        }
    ]

    programs = load_all_accredited_programs()

    assert len(programs) == 1
    assert programs[0]["university"] == "Example University"
    assert programs[0]["website"] == "https://example.edu/psychology"
    assert programs[0]["accreditation_status"] == "APA Accredited, PCSAS Accredited"
    mock_get_aggregated.assert_called_once_with(use_cache=True)
