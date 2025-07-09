# Faculty Recruiting Scraper Roadmap

## Goal

The primary goal of this project is to automate the process of identifying university faculty members who are actively recruiting new graduate students for the upcoming academic year (e.g., 2026).

## Core Tools

*   **Web Crawler:** `crawl4ai` - To navigate and scrape university department and faculty websites.
*   **PDF Parser:** `pymupdf4llm` - To extract text and table data from PDF documents.

## Workflow

### 1. Initial Crawling

*   **Input:** A list of university department or faculty directory URLs.
*   **Action:** Use `crawl4ai` to perform a targeted crawl of the provided URLs.
*   **Keywords:** The crawler will search for pages containing keywords such as:
    *   `new graduate students`
    *   `lab joining`
    *   `2026 admissions cycle`
    *   `faculty recruiting status`
    *   `accepting students`
    *   `openings for new students`

### 2. Content Parsing & Analysis

The crawler will identify two primary types of content: PDF documents and HTML web pages.

#### A. PDF-Based Content

*   **Action:** When a relevant PDF is found, use `pymupdf4llm` to parse its content.
*   **Analysis:**
    *   **Identify relevant documents:** The script will look for tables or text listing faculty names alongside their recruiting status (e.g., "Accepting Students," "Not Accepting," "Contact for details").
    *   **Filter out irrelevant documents:** The script will discard PDFs that contain general student admissions data, handbooks without recruiting information, or other non-relevant content.

#### B. HTML-Based Content (Web Pages)

*   **Action:** The crawler will scan the text of HTML pages for specific phrases.
*   **Analysis:** Look for sections or statements such as:
    *   "Faculty with openings for new students 2025-2026"
    *   "Recruiting students for 2025/2026"
    *   Lists of faculty names under headings related to student admissions.

### 3. Data Extraction

*   **Action:** Once a relevant source (PDF or HTML) is identified, extract the following information:
    *   Faculty Name
    *   Recruiting Status (e.g., "Yes", "No", "Maybe/Contact")
    *   Link to the faculty member's profile or lab page.
    *   The source URL where the information was found.

### 4. Output

*   **Format:** The final output will be a structured data file (e.g., CSV or JSON).
*   **Content:** The file will contain a clean, aggregated list of faculty members and their recruiting status.
