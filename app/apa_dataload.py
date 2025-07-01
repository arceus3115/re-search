from playwright.sync_api import sync_playwright
import csv

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://apps.apa.org/accredsearch/")

        # Select Program Level: Doctoral
        page.check('input[id="ctl00_phContent_rblProgramLevel_1"]')  # Doctoral
        # Select Substantive Area: Clinical Psychology
        page.select_option('select#ctl00_phContent_ddlArea', label="Clinical Psychology")

        # Select Degree: Ph.D.
        page.select_option('select#ctl00_phContent_ddlDegree', label="Ph.D.")

        # Click Search
        page.click('input#ctl00_phContent_btnSubmit')
        page.wait_for_timeout(3000)  # Wait for JS to render results

        # Extract rows
        rows = page.query_selector_all("table#ctl00_phContent_tblResults > tbody > tr")

        with open("clinical_programs.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["State", "Institution", "City", "Program", "Status"])

            for row in rows[1:]:  # Skip header
                cells = row.query_selector_all("td")
                data = [cell.inner_text().strip() for cell in cells]
                writer.writerow(data)

        print("Saved clinical_programs.csv")
        browser.close()

run()