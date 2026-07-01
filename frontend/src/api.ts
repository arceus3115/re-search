import { apiUrl } from './config';

/**
 * Scrapes PCSAS data from the backend API.
 */
export async function scrapePcsasData() {
    const response = await fetch(apiUrl('/api/v1/pcsas'));
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches works by a specific author from the backend API.
 */
export async function fetchAuthorWorks(authorId: string) {
    const response = await fetch(apiUrl(`/api/v1/author_works/${authorId}`));
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches details for a specific author from the backend API.
 */
export async function fetchAuthorDetails(authorId: string) {
    const response = await fetch(apiUrl(`/api/v1/author_details/${authorId}`));
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Discovers and ranks programs based on user profile.
 */
export async function discoverPrograms(page: number = 1, perPage: number = 25, minFitScore: number = 0.0) {
    const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
        min_fit_score: minFitScore.toString()
    });
    const response = await fetch(apiUrl(`/api/v1/programs/discover?${params}`));
    if (!response.ok) {
        const error: any = new Error(`HTTP error! status: ${response.status}`);
        error.status = response.status;
        throw error;
    }
    return response.json();
}

/**
 * Gets detailed research information for a specific program.
 */
export async function getProgramResearch(programId: string) {
    const response = await fetch(apiUrl(`/api/v1/programs/${programId}/research`));
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Gets statistics about accredited programs.
 */
export async function getProgramStats() {
    const response = await fetch(apiUrl('/api/v1/programs/stats'));
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

/**
 * Refreshes cached program data.
 */
export async function refreshPrograms() {
    const response = await fetch(apiUrl('/api/v1/programs/refresh'), { method: 'POST' });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}
