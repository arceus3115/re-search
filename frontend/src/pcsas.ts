
import { scrapePcsasData } from './api';
import { cleanUniversityName, renderCards } from './utils';

/**
 * Renders the PCSAS scraper tab, including the scrape button and results display.
 */
export function renderPcsasTab() {
    const pcsasTabContent = document.getElementById('tab-content-pcsas');
    if (!pcsasTabContent) return;

    pcsasTabContent.innerHTML = `
        <h2>PCSAS</h2>
        <div class="search-elements-group">
            <button id="scrape-pcsas-button">Scrape PCSAS Data</button>
        </div>
        <div id="pcsas-results" class="results-container hidden">
                <div id="pcsas-programs-grid-container">
                </div>
            </div>
    `;

    const scrapePcsasButton = document.getElementById('scrape-pcsas-button');
    const pcsasResultsDiv = document.getElementById('pcsas-results');
    const pcsasProgramsGridContainer = document.getElementById('pcsas-programs-grid-container') as HTMLDivElement;

    console.log('pcsasResultsDiv:', pcsasResultsDiv);
    console.log('pcsasProgramsGridContainer:', pcsasProgramsGridContainer);

    // Handle PCSAS scrape button click
    if (scrapePcsasButton && pcsasResultsDiv && pcsasProgramsGridContainer) {
        scrapePcsasButton.addEventListener('click', async () => {
            pcsasProgramsGridContainer.innerHTML = '<p>Scraping PCSAS data... This may take a moment.</p>';
            pcsasResultsDiv.classList.remove('hidden');
            console.log('pcsasResultsDiv hidden class removed.');

            try {
                const data = await scrapePcsasData();
                const programs = data.programs;

                if (programs && programs.length > 0) {
                    const heading = document.createElement('h3');
                    heading.textContent = 'PCSAS Programs';
                    pcsasResultsDiv.prepend(heading);
                    renderCards(
                        pcsasProgramsGridContainer,
                        programs,
                        (program: any) => `
                            <h4><a href="${program.website}" target="_blank">${cleanUniversityName(program.program_name || 'No Name')}</a></h4>
                            ${program.student_outcomes_link && program.student_outcomes_link !== program.website ? `<p class="small-text"><a href="${program.student_outcomes_link}" target="_blank">Student Outcomes</a></p>` : ''}
                        `,
                        ['university-card', 'card-element'],
                        'university-grid'
                    );
                } else {
                    pcsasProgramsGridContainer.innerHTML = '<p>No PCSAS programs found.</p>';
                }

            } catch (error: unknown) {
                console.error('Error scraping PCSAS data:', error);
                pcsasProgramsGridContainer.innerHTML = `<p>Error scraping PCSAS data: ${(error as Error).message}. Please try again.</p>`;
            }
        });
    }
}
