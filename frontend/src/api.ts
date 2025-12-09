
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
 * Discovers and ranks programs based on user profile.
 * @param {number} page - Page number (default: 1)
 * @param {number} perPage - Results per page (default: 25)
 * @param {number} minFitScore - Minimum fit score (default: 0.0)
 * @returns {Promise<any>} A promise that resolves to the JSON response containing ranked programs.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function discoverPrograms(page: number = 1, perPage: number = 25, minFitScore: number = 0.0) {
    const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
        min_fit_score: minFitScore.toString()
    });
    const response = await fetch(`/api/v1/programs/discover?${params}`);
    if (!response.ok) {
        // Create error with status code for proper handling
        const error: any = new Error(`HTTP error! status: ${response.status}`);
        error.status = response.status;
        throw error;
    }
    return response.json();
}

/**
 * Gets detailed research information for a specific program.
 * @param {string} programId - The program ID.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing research data.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function getProgramResearch(programId: string) {
    const response = await fetch(`/api/v1/programs/${programId}/research`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Gets statistics about accredited programs.
 * @returns {Promise<any>} A promise that resolves to the JSON response containing program statistics.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function getProgramStats() {
    const response = await fetch('/api/v1/programs/stats');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Refreshes cached program data.
 * @returns {Promise<any>} A promise that resolves to the JSON response.
 * @throws {Error} If the network request fails or the response is not OK.
 */
export async function refreshPrograms() {
    const response = await fetch('/api/v1/programs/refresh', { method: 'POST' });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}
