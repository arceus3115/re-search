
import { fetchCrossSearchUniversities } from './api';
import { cleanUniversityName, renderCards } from './utils';

export function renderCrossSearchTab() {
    const tabContentDiv = document.getElementById('tab-content-cross-search');
    if (!tabContentDiv) {
        console.error('Cross-Search tab content div not found!');
        return;
    }

    tabContentDiv.innerHTML = `
        <h2>Cross-Search Universities</h2>
        <div class="search-elements-group">
            <form id="cross-search-form">
                <input type="text" id="cross-search-term" name="search_term" placeholder="Enter search term (e.g., psychology)" required>

                <div class="input-group">
                    <input type="number" id="top-x-works" name="top_x_works" value="10" min="1" max="100" placeholder="Top Works (default 10)">
                </div>

                <button type="submit">Search Common Universities</button>
            </form>
        </div>
        <div id="cross-search-results" class="results-container hidden">
                <div id="cross-search-results-grid">
                </div>
            </div>
    `;

    const crossSearchForm = document.getElementById('cross-search-form');
    const crossSearchResultsContainer = document.getElementById('cross-search-results') as HTMLDivElement;
    const commonUniversitiesGridDisplay = document.getElementById('cross-search-results-grid') as HTMLDivElement;

    crossSearchForm?.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(crossSearchForm as HTMLFormElement);
        const searchTerm = formData.get('search_term') as string;
        const topXWorks = parseInt(formData.get('top_x_works') as string, 10);

        if (!searchTerm) {
            alert('Please enter a search term.');
            return;
        }

        commonUniversitiesGridDisplay.innerHTML = '<p>Loading...</p>';
        crossSearchResultsContainer.classList.remove('hidden');

        try {
            const data = await fetchCrossSearchUniversities(searchTerm, topXWorks);
            if (data.common_universities && data.common_universities.length > 0) {
                const heading = document.createElement('h3');
                heading.textContent = 'Institutions';
                crossSearchResultsContainer.prepend(heading);
                renderCards(
                    commonUniversitiesGridDisplay,
                    data.common_universities,
                    (uni: { name: string, website: string }) => `
                        <a href="${uni.website}" target="_blank">${cleanUniversityName(uni.name)}</a>
                    `,
                    ['university-card', 'card-element'],
                    'university-grid'
                );
            } else {
                commonUniversitiesGridDisplay.innerHTML = '<p>No common universities found.</p>';
            }
        } catch (error) {
            console.error('Error during cross-search:', error);
            commonUniversitiesGridDisplay.innerHTML = '<p>Error fetching common universities.</p>';
        }
    });
}
