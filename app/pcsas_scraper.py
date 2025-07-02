
import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_pcsas():
    """
    Scrapes the PCSAS accredited programs page to extract program information.

    Returns:
        pandas.DataFrame: A DataFrame containing the university, program link, and student outcomes link.
    """
    URL = "https://pcsas.org/pcsas-accredited-programs/"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # Skip header row

    data = []
    for row in rows:
        cols = row.find_all("td")
        
        # Program/University column
        uni_cell = cols[0]
        uni_link_element = uni_cell.find("a")
        uni_name = uni_link_element.text.strip() if uni_link_element else "N/A"
        program_link = uni_link_element["href"] if uni_link_element else "N/A"

        # Program Data column
        outcomes_cell = cols[3]
        outcomes_link_element = outcomes_cell.find("a")
        outcomes_link = outcomes_link_element["href"] if outcomes_link_element else "N/A"

        data.append([uni_name, program_link, outcomes_link])

    df = pd.DataFrame(data, columns=["University", "Program Link", "Student Outcomes Link"])
    return df

if __name__ == "__main__":
    accredited_programs_df = scrape_pcsas()
    print(accredited_programs_df)
