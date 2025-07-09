# re-search

A tool to discover researchers and academic papers.

## Features

*   **Command-line interface (CLI):** Search for academic papers using various filters.
*   **Web interface:** A user-friendly web interface to search for academic papers.
*   **PCSAS Scraper:** Scrapes data from the PCSAS website.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd re-search
    ```

2.  **Install dependencies using Pipenv:**
    ```bash
    pipenv install
    ```

3.  **Activate the virtual environment:**
    ```bash
    pipenv shell
    ```

## Usage

### Command-Line Interface (CLI)

To use the CLI, run the `main.py` script:

```bash
python app/main.py
```

The script will prompt you to enter a search term, start year, country code, and topic IDs.

### Web Application

To run the web application, use the `start` script defined in the `Pipfile` (which uses `uvicorn`):

```bash
pipenv run start
```

This will start a local server. You can access the web application by opening your browser and navigating to `http://127.0.0.1:8000`.

### PCSAS Scraper

The web application also includes a feature to scrape data from the PCSAS website. You can access this feature by navigating to the `/pcsas` endpoint in the web application (e.g., `http://127.0.0.1:8000/pcsas`).

## Known Issues

*   **Previous Button Scrolling:** When clicking the "Previous" button in the academic paper search, the browser briefly scrolls the window to the search term input field before returning to the original scroll position. This is a known browser behavior that has not yet been fully resolved.

## Recent Updates: Interactive Author and Institution Links

This update introduces interactive links for authors and institutions in the search results, enhancing the discoverability of academic networks.

### Backend Enhancements:

*   **Expanded Search Endpoint (`/search`):** The existing search endpoint now includes detailed `authorships` and `institutions` data from OpenAlex, providing author IDs, display names, and institution details like ROR IDs and country codes.
*   **New Author Works Endpoint (`/author_works/<author_id>`):** A new API endpoint has been added to fetch all works by a specific author using their OpenAlex ID. This allows for dynamic retrieval of an author's publication history.

### Frontend Features:

*   **Clickable Author Links:** Author names in search results are now clickable. Clicking an author's name triggers a modal pop-up displaying a list of all works by that author, fetched dynamically from the new backend endpoint.
*   **Direct Institution Links:** Institution names are now direct links to their respective homepages, opening in a new tab for easy access to institutional information.
*   **Interactive Author Modal:** A dedicated modal component handles the display of an author's works, providing a clear and organized view of their publications.

## Roadmap

1.  **Separate Frontend and Backend (Completed):**
    *   The frontend and backend are now separate projects, with the backend serving a RESTful API.
    *   The frontend is implemented using vanilla TypeScript for a lightweight and efficient client-side experience.
    *   Improved code organization and logging have been implemented in both frontend and backend.

2.  **Implement the Core Features:**
    *   Build out the API for searching papers and scraping data.
    *   Implement the frontend for searching papers and displaying the results.

3.  **Add the PI-Finding Feature:**
    *   Add a new module to the backend for finding PIs and their contact information.
    *   Add a new page to the frontend for displaying the PI information.

4.  **Add a Database:**
    *   Set up a PostgreSQL database.
    *   Modify the backend to use the database for storing and retrieving data.

## Next Steps: Advanced PI/Mentor Finding

Building upon the cross-search university feature, the next major step involves a more sophisticated PI/mentor finding capability:

1.  **Clinical Website Navigation:** For universities identified in the cross-search, the system will attempt to navigate to their clinical or research department websites. If a direct link isn't available, it will employ strategies to locate relevant departmental pages.
2.  **PI/Professor Identification:** Once on a departmental page, the system will read the content to identify potential Principal Investigators (PIs) or professors. This will involve parsing faculty directories and research group listings.
3.  **Recruitment Cycle Status:** The system will then attempt to determine if identified PIs/professors are currently taking on new students or mentees for the upcoming research cycle. This may involve looking for specific keywords, application deadlines, or links to recruitment pages.
4.  **Research Alignment Assessment:** The PI/professor's published works (retrieved via OpenAlex) will be cross-referenced with the user's initial search topic to assess their research alignment and relevance.
5.  **Ranked Recommendations:** Finally, the system will provide a ranked list of potential PI/mentor candidates, prioritizing those who best fit the search criteria, are actively recruiting, and have strong research alignment with the specified topic.