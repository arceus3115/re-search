import requests
from bs4 import BeautifulSoup


def scrape_pcsas():
    """Scrapes the PCSAS accredited programs page to extract program information.

    This function sends an HTTP GET request to the PCSAS website, parses the HTML
    content to find the table of accredited programs, and extracts relevant details
    such as program name, website, and student outcomes link.

    Returns:
        list: A list of dictionaries, where each dictionary represents a program
              and contains the keys 'program_name', 'website', and 'student_outcomes_link'.
              Returns an empty list if the table is not found or no programs are extracted.
    """
    URL = "https://pcsas.org/pcsas-accredited-programs/"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]  # Skip header row

    programs_data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:  # Ensure there are enough columns
            continue

        # Program/University column
        uni_cell = cols[0]
        uni_link_element = uni_cell.find("a")
        program_name = uni_link_element.text.strip() if uni_link_element else "N/A"
        program_website = uni_link_element["href"] if uni_link_element else "N/A"

        # Student Outcomes Link column
        outcomes_cell = cols[3]
        outcomes_link_element = outcomes_cell.find("a")
        student_outcomes_link = (
            outcomes_link_element["href"] if outcomes_link_element else "N/A"
        )

        programs_data.append(
            {
                "program_name": program_name,
                "website": program_website,
                "student_outcomes_link": student_outcomes_link,
            }
        )

    return programs_data
