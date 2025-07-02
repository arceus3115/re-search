document.addEventListener('DOMContentLoaded', () => {
    const appDiv = document.getElementById('root');
    if (!appDiv) {
        console.error('Root element not found!');
        return;
    }

    function renderLandingPage(appDiv: HTMLElement) {
        appDiv.innerHTML = `
            <div class="landing-page">
                <h1>Research Network Hub</h1>
                <p>Welcome to your central hub for academic research tools.</p>
                <hr>
                <h2>Available Tools</h2>
                <div class="tool-list">
                    <button class="tool-button" data-tool="search">Academic Paper Search</button>
                    <button class="tool-button" data-tool="pcsas">PCSAS Scraper</button>
                </div>
                <hr>
                <h2>Your Network Dashboard</h2>
                <div id="network-animation-placeholder" style="height: 300px; background-color: #f0f0f0; display: flex; justify-content: center; align-items: center; border-radius: 8px;">
                    <p>Cool Network Animation Placeholder</p>
                </div>
            </div>
        `;

        document.querySelectorAll('.tool-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const tool = (event.target as HTMLElement).dataset.tool;
                if (tool) {
                    renderApp(appDiv, tool);
                }
            });
        });
    }

    async function renderApp(appDiv: HTMLElement, initialTab: string = 'search') {
        appDiv.innerHTML = `
            <div class="app-header">
                <div class="logo">Research Network</div>
                <div class="tabs">
                    <button class="tab-button" data-tab="search">Academic Paper Search</button>
                    <button class="tab-button" data-tab="pcsas">PCSAS Scraper</button>
                </div>
            </div>
            <div class="app-container">
                <div id="tab-content-search" class="tab-content">
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
                    <hr>
                    <div id="search-results"></div>
                </div>
                <div id="tab-content-pcsas" class="tab-content">
                    <h2>PCSAS Scraper</h2>
                    <button id="scrape-pcsas-button">Scrape PCSAS Data</button>
                    <div id="pcsas-results"></div>
                </div>
            </div>
        `;

        const topicIdsGrid = document.getElementById('topic-ids-grid');
        const searchForm = document.getElementById('search-form');
        const searchResultsDiv = document.getElementById('search-results');
        const scrapePcsasButton = document.getElementById('scrape-pcsas-button');
        const pcsasResultsDiv = document.getElementById('pcsas-results');
        const logoElement = document.querySelector('.app-header .logo') as HTMLElement; // Cast to HTMLElement

        let selectedTopicIds: string[] = [];

        // Fetch and populate topic IDs grid
        try {
            const response = await fetch('/api/v1/fields');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
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
            appDiv.innerHTML += '<p>Failed to load fields. Please check the backend server.</p>';
        }

        // Handle search form submission
        if (searchForm) {
            searchForm.addEventListener('submit', async (event) => {
                event.preventDefault();

                const formData = new FormData(searchForm as HTMLFormElement);
                const searchTerm = formData.get('search_term') as string;
                const fromYear = formData.get('from_year') ? parseInt(formData.get('from_year') as string) : 1980;
                const countryCode = formData.get('country_code') as string || 'US';
                const topicIds = selectedTopicIds;

                try {
                    const response = await fetch('/api/v1/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            search_term: searchTerm,
                            from_year: fromYear,
                            country_code: countryCode,
                            topic_ids: topicIds,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
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

                } catch (error) {
                    console.error('Error during search:', error);
                    if (searchResultsDiv) searchResultsDiv.innerHTML = '<p>Error performing search. Please try again.</p>';
                }
            });
        }

        // Handle PCSAS scrape button click
        if (scrapePcsasButton) {
            scrapePcsasButton.addEventListener('click', async () => {
                if (pcsasResultsDiv) {
                    pcsasResultsDiv.innerHTML = '<p>Scraping PCSAS data... This may take a moment.</p>';
                }
                try {
                    const response = await fetch('/api/v1/pcsas');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    const programs = data.programs;

                    if (pcsasResultsDiv) {
                        pcsasResultsDiv.innerHTML = '<h3>PCSAS Programs:</h3>';
                        if (programs && programs.length > 0) {
                            const ul = document.createElement('ul');
                            programs.forEach((program: any) => {
                                const li = document.createElement('li');
                                li.innerHTML = `
                                    <h4><a href="${program.website}" target="_blank">${program.program_name || 'No Name'}</a></h4>
                                    ${program.student_outcomes_link && program.student_outcomes_link !== program.website ? `<p><a href="${program.student_outcomes_link}" target="_blank">View Student Outcomes</a></p>` : ''}
                                `;
                                ul.appendChild(li);
                            });
                            pcsasResultsDiv.appendChild(ul);
                        } else {
                            pcsasResultsDiv.innerHTML += '<p>No PCSAS programs found.</p>';
                        }
                    }

                } catch (error) {
                    console.error('Error scraping PCSAS data:', error);
                    if (pcsasResultsDiv) pcsasResultsDiv.innerHTML = '<p>Error scraping PCSAS data. Please try again.</p>';
                }
            });
        }

        // Tab switching logic
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const tabId = (event.target as HTMLElement).dataset.tab;
                document.querySelectorAll('.tab-content').forEach(content => {
                    (content as HTMLElement).style.display = 'none';
                });
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                if (tabId) {
                    const activeContent = document.getElementById(`tab-content-${tabId}`);
                    if (activeContent) {
                        (activeContent as HTMLElement).style.display = 'block';
                    }
                    (event.target as HTMLElement).classList.add('active');
                }
            });
        });

        // Make logo clickable to return to hub
        if (logoElement) {
            logoElement.style.cursor = 'pointer'; // Indicate it's clickable
            logoElement.addEventListener('click', () => {
                renderLandingPage(appDiv);
            });
        }

        // Activate initial tab
        const initialTabButton = document.querySelector(`.tab-button[data-tab="${initialTab}"]`) as HTMLElement;
        if (initialTabButton) {
            initialTabButton.click();
        }
    }

    // Initial render: landing page
    renderLandingPage(appDiv);
});