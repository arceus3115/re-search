from bs4 import BeautifulSoup

from app.scrapers.pcsas_scraper import _parse_pcsas_table
from app.utils.exceptions import ScrapingError
from app.utils.url_utils import normalize_url, unwrap_safelinks


def test_unwrap_safelinks():
    wrapped = (
        "https://nam10.safelinks.protection.outlook.com/?url="
        "https%3A%2F%2Fpsychology.example.edu%2Foutcomes.pdf"
    )
    assert unwrap_safelinks(wrapped) == "https://psychology.example.edu/outcomes.pdf"


def test_normalize_url_rejects_placeholder():
    assert normalize_url("N/A") is None
    assert normalize_url("  https://example.edu  ") == "https://example.edu"


def test_parse_pcsas_table_from_fixture():
    with open("app/fixtures/pcsas_table.html", "r", encoding="utf-8") as handle:
        html = handle.read()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    # Fixture has fewer rows than production minimum; patch threshold for unit test.
    import app.scrapers.pcsas_scraper as pcsas_module

    original_min = pcsas_module.MIN_EXPECTED_PROGRAMS
    pcsas_module.MIN_EXPECTED_PROGRAMS = 2
    try:
        programs = _parse_pcsas_table(table)
    finally:
        pcsas_module.MIN_EXPECTED_PROGRAMS = original_min

    assert len(programs) == 2
    assert programs[0]["program_name"] == "Example University"
    assert programs[0]["website"] == "https://psychology.example.edu/clinical"
    assert (
        programs[0]["student_outcomes_link"]
        == "https://psychology.example.edu/outcomes.pdf"
    )
    assert programs[0]["review_date"] == "01/01/2024"
    assert programs[0]["accreditation_status"] == "Accredited"


def test_parse_pcsas_table_raises_when_empty():
    soup = BeautifulSoup("<table><tr><th>Program</th></tr></table>", "html.parser")
    try:
        _parse_pcsas_table(soup.find("table"))
        assert False, "Expected ScrapingError"
    except ScrapingError:
        pass
