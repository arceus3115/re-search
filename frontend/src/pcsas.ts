
import { scrapePcsasData } from './api';

/**
 * Renders the PCSAS scraper tab, including the scrape button and results display.
 */
export function renderPcsasTab() {
    const pcsasTabContent = document.getElementById('tab-content-pcsas');
    if (!pcsasTabContent) return;

    pcsasTabContent.innerHTML = `
        <h2>PCSAS</h2>
        <button id="scrape-pcsas-button">Scrape PCSAS Data</button>
        <div id="pcsas-results"></div>
    `;

    const scrapePcsasButton = document.getElementById('scrape-pcsas-button');
    const pcsasResultsDiv = document.getElementById('pcsas-results');

    // Handle PCSAS scrape button click
    if (scrapePcsasButton) {
        scrapePcsasButton.addEventListener('click', async () => {
            if (pcsasResultsDiv) {
                pcsasResultsDiv.innerHTML = '<p>Scraping PCSAS data... This may take a moment.</p>';
            }
            try {
                const data = await scrapePcsasData();
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

            } catch (error: unknown) {
                console.error('Error scraping PCSAS data:', error);
                if (pcsasResultsDiv) pcsasResultsDiv.innerHTML = `<p>Error scraping PCSAS data: ${(error as Error).message}. Please try again.</p>`;
            }
        });
    }
}
