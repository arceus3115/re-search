
import { scrapePcsasData } from './api';
import { cleanUniversityName, renderCards } from './utils';

/**
 * Renders the PCSAS scraper tab, including the scrape button and results display.
 */
export function renderPcsasTab() {
    const pcsasTabContent = document.getElementById('tab-content-pcsas');
    if (!pcsasTabContent) return;

    pcsasTabContent.innerHTML = `
        <div class="agents-container" style="max-width: 1200px; margin: 0 auto; padding: 2rem;">
            <h2 style="margin-bottom: 1.5rem;">PCSAS</h2>
            <p style="margin-bottom: 2rem; color: #666;">Scrape and view PCSAS-accredited Clinical Psychology programs.</p>

            <div class="agent-form" style="background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 2rem; margin-bottom: 2rem;">
                <h3 style="margin-top: 0; margin-bottom: 1rem;">Scrape PCSAS Data</h3>
                <button id="scrape-pcsas-button" class="btn-primary" style="width: 100%; padding: 0.75rem; font-size: 1rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Scrape PCSAS Data</button>
            </div>

            <div id="pcsas-results" class="results-container hidden" style="background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <div id="pcsas-programs-grid-container">
                </div>
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
                    heading.style.marginTop = '0';
                    heading.style.marginBottom = '1rem';
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
