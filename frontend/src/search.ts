
import { fetchFields, searchPapers } from './api';

let currentPage = 0;
let currentSearchTerm: string = '';
let currentFromYear: number = 1980;
let currentCountryCode: string = 'US';
let currentTopicIds: string[] = [];
const searchResultsCache: { [key: number]: any[] } = {};
let isLoading = false;
const RESULTS_PER_PAGE = 25;

/**
 * Renders a list of academic works into the search results div.
 * @param {any[]} works - An array of academic work objects to render.
 * @param {HTMLElement} resultsContainer - The div element to render the results into.
 */
function renderWorks(works: any[], resultsContainer: HTMLElement) {
    console.log(`renderWorks called with ${works.length} works.`);
    resultsContainer.innerHTML = ''; // Always clear previous results

    if (works && works.length > 0) {
        const ul = document.createElement('ul');
        console.log('Created ul element:', ul);
        works.forEach((work: any) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <h4>${work.title || 'No Title'}</h4>
                <p><strong>Authors:</strong> ${work.authorships.map((a: any) => `<span class="author-link" data-author-id="${a.author.id}" data-author-name="${a.author.display_name}">${a.author.display_name}</span>`).join(', ') || 'N/A'}</p>
                <p><strong>Affiliations:</strong> ${work.authorships.flatMap((a: any) => a.institutions.map((i: any) => {
                    console.log('Institution:', i.display_name, 'Homepage URL:', i.homepage_url);
                    return i.homepage_url ? `<a href="${i.homepage_url}" target="_blank">${i.display_name}</a>` : i.display_name;
                })).filter((name: string) => name).join(', ') || 'N/A'}</p>
                <p><strong>FWCI:</strong> ${work.fwci || 'N/A'}</p>
            `;
            ul.appendChild(li);
        });
        resultsContainer.appendChild(ul);
    } else {
        resultsContainer.innerHTML = '<p>No results found for your search.</p>';
    }
}



async function fetchAndRenderPage(page: number, searchResultsDiv: HTMLElement) {
    console.log(`fetchAndRenderPage called for page: ${page}`);
    if (isLoading) {
        console.log('Already loading, returning.');
        return;
    }
    isLoading = true;

    currentPage = page; // Update currentPage immediately

    const resultsContainer = searchResultsDiv.querySelector('#results-container') as HTMLElement;
    if (!resultsContainer) {
        console.error('Results container not found!');
        isLoading = false;
        return;
    }

    resultsContainer.innerHTML = '<p>Loading results...</p>'; // Show loading indicator within results area

    // Hide pagination controls while loading
    const allPaginationControls = document.querySelectorAll('.pagination-controls') as NodeListOf<HTMLElement>;
    console.log('Hiding pagination controls.');
    allPaginationControls.forEach(control => control.style.display = 'none');

    try {
        let works: any[] = [];
        let hasNextPage = false;

        if (searchResultsCache[page]) {
            console.log(`Page ${page} found in cache.`);
            works = searchResultsCache[page];
            delete searchResultsCache[page]; // Consume from cache
        } else {
            console.log(`Fetching page ${page} from API.`);
            const data = await searchPapers(currentSearchTerm, currentFromYear, currentCountryCode, currentTopicIds, page, RESULTS_PER_PAGE);
            works = data.works;
        }

        console.log(`Fetched ${works.length} works for page ${page}.`);
        // Determine if there's a next page based on the number of results received
        hasNextPage = works.length === RESULTS_PER_PAGE;
        console.log(`Has next page: ${hasNextPage}`);

        renderWorks(works, resultsContainer);

        // Update the disabled state of the existing buttons
        const prevButtons = document.querySelectorAll<HTMLButtonElement>('[id^="prev-button-"]');
        const nextButtons = document.querySelectorAll<HTMLButtonElement>('[id^="next-button-"]');

        console.log('Updating button disabled states.');
        prevButtons.forEach(button => button.disabled = currentPage === 1);
        nextButtons.forEach(button => button.disabled = !hasNextPage);

        // Show pagination controls if there are results, otherwise keep hidden
        if (works.length > 0) {
            console.log('Showing pagination controls.');
            allPaginationControls.forEach(control => control.style.display = 'flex');
        } else {
            console.log('No works found, keeping pagination controls hidden.');
        }

        preloadPages(); // Preload next pages

    } catch (error: unknown) {
        console.error('Error during search:', error);
        resultsContainer.innerHTML = `<p>Error performing search: ${(error as Error).message}. Please try again.</p>`;
    } finally {
        isLoading = false;
        console.log('Loading finished.');
    }
}

/**
 * Preloads the next 4 pages of search results into the cache.
 * @param {HTMLElement} searchResultsDiv - The div to render results into (used for context).
 */
async function preloadPages() {
    console.log('Starting preloadPages. Current page:', currentPage);
    for (let i = 1; i <= 4; i++) {
        const pageToPreload = currentPage + i;
        console.log(`Attempting to preload page ${pageToPreload}.`);
        // Only preload if not already in cache and within a reasonable limit (e.g., 10000 results / 25 per page = 400 pages)
        if (!searchResultsCache[pageToPreload] && pageToPreload <= 400) {
            try {
                console.log(`Fetching preload page ${pageToPreload} from API.`);
                const data = await searchPapers(currentSearchTerm, currentFromYear, currentCountryCode, currentTopicIds, pageToPreload, RESULTS_PER_PAGE);
                // Only cache if results were returned (i.e., not an empty page indicating end of results)
                if (data.works && data.works.length > 0) {
                    searchResultsCache[pageToPreload] = data.works;
                    console.log(`Preloaded page ${pageToPreload} with ${data.works.length} works.`);
                } else {
                    console.log(`Preload page ${pageToPreload} returned no works. Stopping preloading.`);
                    // If an empty page is returned, it means we've reached the end of results
                    // No need to preload further pages from this point
                    break;
                }
            } catch (error) {
                console.warn(`Failed to preload page ${pageToPreload}:`, error);
                // Stop preloading if an error occurs to avoid cascading issues
                break;
            }
        } else if (searchResultsCache[pageToPreload]) {
            console.log(`Page ${pageToPreload} already in cache, skipping preload.`);
        } else {
            console.log(`Page ${pageToPreload} is beyond preload limit (400 pages), skipping preload.`);
        }
    }
}

/**
 * Renders the academic paper search tab, including the search form and results display.
 */
export function renderSearchTab() {
    const searchTabContent = document.getElementById('tab-content-search');
    if (!searchTabContent) return;

    searchTabContent.innerHTML = `
        <h2>Search Academic Papers</h2>
        <form id="search-form">
            <label for="search-term">Search Term:</label>
            <input type="text" id="search-term" name="search_term" required><br><br>

            <label for="from-year">From Year (default 1980):</label>
            <input type="number" id="from-year" name="from_year" value="1980"><br><br>

            <label for="country-code">Country Code (default US):</label>
            <input type="text" id="country-code" name="country_code" value="US"><br><br>

            <h3>Select Topic IDs:</h3>
            <div id="topic-ids-grid"></div>
            <br>

            <button type="submit">Search</button>
        </form>
        <div class="search-results-padding"></div> <!-- Padding div -->
        <div id="search-results">
            <div id="top-pagination-controls" class="pagination-controls"></div>
            <div id="results-container"></div>
            <div id="bottom-pagination-controls" class="pagination-controls"></div>
        </div>
    `;

    const topicIdsGrid = document.getElementById('topic-ids-grid');
    const searchForm = document.getElementById('search-form');
    const searchResultsDiv = document.getElementById('search-results');
    const topPaginationControls = document.getElementById('top-pagination-controls');
    const bottomPaginationControls = document.getElementById('bottom-pagination-controls');
    const resultsContainer = document.getElementById('results-container');

    let selectedTopicIds: string[] = [];

    // Helper to create and append buttons
    const setupPaginationButtons = (container: HTMLElement) => {
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.id = `prev-button-${container.id}`;
        prevButton.type = 'button'; // Explicitly set type to button
        prevButton.addEventListener('click', () => {
            console.log(`Previous button clicked. Current page: ${currentPage}`);
            fetchAndRenderPage(currentPage - 1, searchResultsDiv as HTMLElement);
        });
        container.appendChild(prevButton);

        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.id = `next-button-${container.id}`;
        nextButton.type = 'button'; // Explicitly set type to button
        nextButton.addEventListener('click', () => {
            console.log(`Next button clicked. Current page: ${currentPage}`);
            fetchAndRenderPage(currentPage + 1, searchResultsDiv as HTMLElement);
        });
        container.appendChild(nextButton);
    };

    if (topPaginationControls) {
        setupPaginationButtons(topPaginationControls);
        console.log('Top pagination controls setup.', topPaginationControls);
    }
    if (bottomPaginationControls) {
        setupPaginationButtons(bottomPaginationControls);
        console.log('Bottom pagination controls setup.', bottomPaginationControls);
    }

    // Fetch and populate topic IDs grid
    (async () => {
        try {
            const data = await fetchFields();
            const fields = data.fields;

            if (topicIdsGrid) {
                for (const id in fields) {
                    const topicButton = document.createElement('div');
                    topicButton.classList.add('topic-button');
                    topicButton.dataset.topicId = id; // Store ID in data attribute
                    topicButton.textContent = fields[id];

                    topicButton.addEventListener('click', () => {
                        topicButton.classList.toggle('selected');
                        if (topicButton.classList.contains('selected')) {
                            selectedTopicIds.push(id);
                        } else {
                            selectedTopicIds = selectedTopicIds.filter(topic => topic !== id);
                        }
                    });
                    topicIdsGrid.appendChild(topicButton);
                }
            }

        } catch (error) {
            console.error('Error fetching fields:', error);
            if (searchTabContent) searchTabContent.innerHTML += '<p>Failed to load fields. Please check the backend server.</p>';
        }
    })();

    // Handle search form submission
    if (searchForm) {
        searchForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const formData = new FormData(searchForm as HTMLFormElement);
            currentSearchTerm = formData.get('search_term') as string;
            currentFromYear = formData.get('from_year') ? parseInt(formData.get('from_year') as string) : 1980;
            currentCountryCode = formData.get('country_code') as string || 'US';
            currentTopicIds = selectedTopicIds;

            // Reset state for new search
            currentPage = 0;
            for (const key in searchResultsCache) {
                delete searchResultsCache[key];
            }

            if (searchResultsDiv) {
                // Clear previous results and ensure results container is empty
                const resultsContainer = searchResultsDiv.querySelector('#results-container') as HTMLElement;
                if (resultsContainer) {
                    resultsContainer.innerHTML = '';
                }
                // Reset button states and hide controls
            document.querySelectorAll<HTMLButtonElement>('[id^="prev-button-"]').forEach(button => button.disabled = true);
            document.querySelectorAll<HTMLButtonElement>('[id^="next-button-"]').forEach(button => button.disabled = true);
            document.querySelectorAll('.pagination-controls').forEach(control => (control as HTMLElement).style.display = 'none');

            if (searchResultsDiv) {
                // Clear previous results and ensure results container is empty
                const resultsContainer = searchResultsDiv.querySelector('#results-container') as HTMLElement;
                if (resultsContainer) {
                    resultsContainer.innerHTML = '';
                }
                await fetchAndRenderPage(1, searchResultsDiv); // Fetch and render first page
            }
            }
        });
    }
}

