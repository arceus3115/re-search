
import { fetchFields, searchPapers } from './api';

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
        <div id="search-results"></div>
    `;

    const topicIdsGrid = document.getElementById('topic-ids-grid');
    const searchForm = document.getElementById('search-form');
    const searchResultsDiv = document.getElementById('search-results');

    let selectedTopicIds: string[] = [];

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
            const searchTerm = formData.get('search_term') as string;
            const fromYear = formData.get('from_year') ? parseInt(formData.get('from_year') as string) : 1980;
            const countryCode = formData.get('country_code') as string || 'US';
            const topicIds = selectedTopicIds;

            if (searchResultsDiv) {
                searchResultsDiv.innerHTML = '<p>Searching...</p>'; // Loading indicator
            }

            try {
                const data = await searchPapers(searchTerm, fromYear, countryCode, topicIds);
                const works = data.works;

                if (searchResultsDiv) {
                    searchResultsDiv.innerHTML = '<h3>Search Results:</h3>';
                    if (works && works.length > 0) {
                        const ul = document.createElement('ul');
                        works.forEach((work: any) => {
                            const li = document.createElement('li');
                            li.innerHTML = `
                                <h4>${work.title || 'No Title'}</h4>
                                <p><strong>Authors:</strong> ${work.authorships.map((a: any) => a.author.display_name).join(', ') || 'N/A'}</p>
                                <p><strong>Affiliations:</strong> ${work.authorships.flatMap((a: any) => a.institutions.map((i: any) => i.display_name)).filter((name: string) => name).join(', ') || 'N/A'}</p>
                                <p><strong>FWCI:</strong> ${work.fwci || 'N/A'}</p>
                            `;
                            ul.appendChild(li);
                        });
                        searchResultsDiv.appendChild(ul);
                    } else {
                        searchResultsDiv.innerHTML += '<p>No results found for your search.</p>';
                    }
                }

            } catch (error: unknown) {
                console.error('Error during search:', error);
                if (searchResultsDiv) searchResultsDiv.innerHTML = `<p>Error performing search: ${(error as Error).message}. Please try again.</p>`;
            }
        });
    }
}
