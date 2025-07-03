
/**
 * Fetches the list of available academic fields from the backend API.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing the fields.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function fetchFields() {
    const response = await fetch('/api/v1/fields');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Sends a search request for academic papers to the backend API.
 * @param {string} searchTerm - The main search query.
 * @param {number} fromYear - The starting year for the search.
 * @param {string} countryCode - The country code for filtering results.
 * @param {string[]} topicIds - An array of topic IDs for filtering results.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing the search results.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function searchPapers(searchTerm: string, fromYear: number, countryCode: string, topicIds: string[], page: number, perPage: number) {
    const queryParams = new URLSearchParams({
        search_term: searchTerm,
        from_year: fromYear.toString(),
        country_code: countryCode,
        page: page.toString(),
        per_page: perPage.toString()
    });

    // Append topic_ids as multiple parameters
    topicIds.forEach(id => queryParams.append('topic_ids', id));

    const response = await fetch(`/api/v1/search?${queryParams.toString()}`);

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Scrapes PCSAS data from the backend API.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing the PCSAS data.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function scrapePcsasData() {
    const response = await fetch('/api/v1/pcsas');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}
