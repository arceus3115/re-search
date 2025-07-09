
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

/**
 * Fetches works by a specific author from the backend API.
 * This endpoint is used to retrieve a list of academic works associated with a given author ID.
 * @param {string} authorId - The OpenAlex ID of the author.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing the author's works.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function fetchAuthorWorks(authorId: string) {
    const response = await fetch(`/api/v1/author_works/${authorId}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches details for a specific author from the backend API.
 * This endpoint provides comprehensive information about an author, including their affiliations.
 * @param {string} authorId - The OpenAlex ID of the author.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing the author's details.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function fetchAuthorDetails(authorId: string) {
    const response = await fetch(`/api/v1/author_details/${authorId}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches common universities between top research works and PCSAS accredited programs.
 * @param {string} searchTerm - The search term for academic papers.
 * @param {number} topXWorks - The number of top works to consider for affiliation extraction.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing the common universities.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function fetchCrossSearchUniversities(searchTerm: string, topXWorks: number): Promise<{ common_universities: { name: string, website: string }[] }> {
    const queryParams = new URLSearchParams({
        search_term: searchTerm,
        top_x_works: topXWorks.toString()
    });
    const response = await fetch(`/api/v1/cross_search_universities?${queryParams.toString()}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}
