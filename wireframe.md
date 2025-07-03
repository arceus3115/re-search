# Feature: Interactive Author and Institution Links

## 1. Backend Changes

### 1.1. Modify Existing Endpoint (`/search`)

*   **File:** `backend/app/academic_network.py` (or wherever the search logic is)
*   **Change:** When fetching works from OpenAlex, ensure the following fields are included in the response for each work:
    *   `authorships`: This array contains author information. For each author, we need:
        *   `author.id`: The OpenAlex author ID.
        *   `author.display_name`: The author's name.
        *   `institutions`: This array contains institution information. For each institution, we need:
            *   `display_name`: The institution's name.
            *   `ror`: The ROR ID of the institution.
            *   `country_code`
            *   `type`

### 1.2. Create New Endpoint (`/author_works`)

*   **File:** `backend/app/web_app.py` (or wherever the Flask routes are defined)
*   **Endpoint:** `/author_works/<author_id>`
*   **Method:** `GET`
*   **Functionality:**
    *   Takes an `author_id` as a parameter.
    *   Uses the OpenAlex API to fetch all works by that author.
    *   The endpoint should look something like: `https://api.openalex.org/works?filter=author.id:<author_id>`
    *   Returns a JSON list of works, similar to the `/search` endpoint.

## 2. Frontend Changes

### 2.1. Update Search Result Rendering

*   **File:** `frontend/src/ui.ts` (or wherever the search results are rendered)
*   **Change:**
    *   For each work in the search results:
        *   Render the author names as clickable links or buttons.
        *   Each author link should have a `data-author-id` attribute containing the author's OpenAlex ID.
        *   Render the institution names as `<a>` tags.
        *   The `href` of the institution link should be the institution's homepage URL.
        *   The `target` of the institution link should be `_blank` to open in a new tab.

### 2.2. Implement Author Pop-up (Modal)

*   **File:** `frontend/src/ui.ts` (or a new `modal.ts` file)
*   **Functionality:**
    *   Create a modal component that is initially hidden.
    *   The modal should have a title (e.g., "Works by [Author Name]") and a list to display the works.
    *   Add a close button to the modal.

### 2.3. Implement Pop-up Logic

*   **File:** `frontend/src/index.ts` (or wherever the main event listeners are)
*   **Change:**
    *   Add a click event listener to the document that listens for clicks on elements with the `data-author-id` attribute.
    *   When an author link is clicked:
        1.  Prevent the default link behavior.
        2.  Get the `author_id` from the `data-author-id` attribute.
        3.  Get the author's name from the link's text content.
        4.  Make a `fetch` request to the new `/author_works/<author_id>` backend endpoint.
        5.  Update the modal title with the author's name.
        6.  Render the fetched works in the modal's list.
        7.  Show the modal.
    *   Add a click event listener to the modal's close button to hide the modal.

## 3. Data Flow Summary

1.  User performs a search.
2.  `frontend/src/search.ts` calls the `/search` endpoint on the backend.
3.  `backend/app/web_app.py` receives the request and calls the OpenAlex API.
4.  The backend processes the OpenAlex response and returns a JSON list of works, including author and institution data.
5.  `frontend/src/ui.ts` renders the search results, creating interactive links for authors and institutions.
6.  User clicks on an author link.
7.  `frontend/src/index.ts` captures the click event.
8.  `frontend/src/api.ts` (or similar) calls the `/author_works/<author_id>` endpoint.
9.  `backend/app/web_app.py` receives the request and calls the OpenAlex API to get the author's works.
10. The backend returns a JSON list of the author's works.
11. `frontend/src/ui.ts` (or `modal.ts`) renders the works in the pop-up modal.
12. User clicks on an institution link.
13. The browser opens the institution's homepage in a new tab.
