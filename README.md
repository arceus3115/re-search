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