/**
 * PI Finder Agent UI component
 */

export interface AgentPI_Candidate {
    name: string;
    openalex_id: string;
    institution: string;
    relevance_score: number;
    topics: string[];
    email?: string;
    accepting_phd_students?: boolean;
    research_description?: string;
    lab_goals?: string;
    acceptance_status: string;
    acceptance_confidence: number;
    personal_homepage?: string;
    recent_publications_count: number;
    country?: string;
}

/**
 * Renders the PI Finder Agent tab
 */
export function renderAgentsPiFinderTab(): void {
    const container = document.getElementById('tab-content-agents-pi-finder');
    if (!container) return;

    container.innerHTML = `
        <div class="agents-container" style="max-width: 1200px; margin: 0 auto; padding: 2rem;">
            <h2 style="margin-bottom: 1.5rem;">PI Finder Agent</h2>
            <p style="margin-bottom: 2rem; color: #666;">Find PIs at accredited Clinical Psychology programs matching your specialties and techniques.</p>

            <div class="agent-form" style="background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 2rem; margin-bottom: 2rem;">
                <h3 style="margin-top: 0;">Search Parameters</h3>

                <div style="margin-bottom: 1.5rem;">
                    <label for="agent-specialties" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Research Specialties (comma-separated)</label>
                    <input type="text" id="agent-specialties" class="form-control"
                        placeholder="e.g., memory, trauma, depression, anxiety"
                        style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                    <small style="color: #666;">Enter specialties separated by commas</small>
                </div>

                <div style="margin-bottom: 1.5rem;">
                    <label for="agent-techniques" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Techniques (comma-separated, optional)</label>
                    <input type="text" id="agent-techniques" class="form-control"
                        placeholder="e.g., MRI, EEG, fMRI, TMS"
                        style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                    <small style="color: #666;">Enter techniques separated by commas</small>
                </div>

                <div style="margin-bottom: 1.5rem;">
                    <label for="agent-country" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Country Filter (optional)</label>
                    <select id="agent-country" class="form-control" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                        <option value="">All Countries</option>
                        <option value="US">United States</option>
                        <option value="GB">United Kingdom</option>
                        <option value="CA">Canada</option>
                        <option value="AU">Australia</option>
                    </select>
                </div>

                <button id="agent-search-btn" class="btn-primary" style="width: 100%; padding: 0.75rem; font-size: 1rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Search for PIs
                </button>
            </div>

            <div id="agent-results-container" style="display: none;">
                <div style="background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                    <h3 style="margin-top: 0;">Results</h3>
                    <div id="agent-results-info" style="margin-bottom: 1rem;"></div>
                    <div id="agent-pagination-info" style="margin-top: 1rem;"></div>
                </div>
                <div id="agent-candidates-list" class="candidates-list"></div>
            </div>
        </div>
    `;

    // Setup search button
    const searchBtn = document.getElementById('agent-search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }
}

let currentPage = 1;
let currentResults: any = null;

async function handleSearch(): Promise<void> {
    const specialtiesInput = document.getElementById('agent-specialties') as HTMLInputElement;
    const techniquesInput = document.getElementById('agent-techniques') as HTMLInputElement;
    const countrySelect = document.getElementById('agent-country') as HTMLSelectElement;
    const resultsContainer = document.getElementById('agent-results-container');
    const candidatesList = document.getElementById('agent-candidates-list');

    if (!specialtiesInput || !resultsContainer || !candidatesList) return;

    const specialtiesStr = specialtiesInput.value.trim();
    if (!specialtiesStr) {
        alert('Please enter at least one specialty');
        return;
    }

    // Parse inputs
    const specialties = specialtiesStr.split(',').map(s => s.trim()).filter(s => s);
    const techniquesStr = techniquesInput?.value.trim() || '';
    const techniques = techniquesStr ? techniquesStr.split(',').map(t => t.trim()).filter(t => t) : [];
    const country = countrySelect?.value || undefined;

    // Show loading
    candidatesList.innerHTML = '<div class="loading">Searching for PIs... This may take a minute.</div>';
    resultsContainer.style.display = 'block';
    currentPage = 1;

    try {
        const response = await fetch(`/api/v1/agents/pi-finder/search?page=${currentPage}&per_page=25`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                specialties,
                techniques,
                country_filter: country
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to search for PIs');
        }

        const result = await response.json();
        currentResults = result;
        renderResults(result);
    } catch (error: any) {
        candidatesList.innerHTML = `<div style="color: red; padding: 1rem;">Error: ${error.message}</div>`;
    }
}

function renderResults(result: any): void {
    const candidatesList = document.getElementById('agent-candidates-list');
    const resultsInfo = document.getElementById('agent-results-info');
    const paginationInfo = document.getElementById('agent-pagination-info');

    if (!candidatesList || !resultsInfo) return;

    const candidates: AgentPI_Candidate[] = result.candidates || [];
    const pagination = result.pagination || {};

    // Update info
    resultsInfo.innerHTML = `<strong>Found ${pagination.total_count || 0} candidates</strong>`;

    if (paginationInfo) {
        paginationInfo.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>Page ${pagination.page || 1} of ${pagination.total_pages || 1}</span>
                <div>
                    ${pagination.has_previous ? `<button id="agent-prev-page" class="btn-secondary" style="margin-right: 0.5rem;">Previous</button>` : ''}
                    ${pagination.has_next ? `<button id="agent-next-page" class="btn-secondary">Next</button>` : ''}
                </div>
            </div>
        `;

        // Setup pagination buttons
        const prevBtn = document.getElementById('agent-prev-page');
        const nextBtn = document.getElementById('agent-next-page');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    handleSearch();
                }
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (pagination.has_next) {
                    currentPage++;
                    handleSearch();
                }
            });
        }
    }

    // Render candidates
    if (candidates.length === 0) {
        candidatesList.innerHTML = '<div style="padding: 2rem; text-align: center; color: #666;">No candidates found. Try adjusting your search parameters.</div>';
        return;
    }

    candidatesList.innerHTML = candidates.map((candidate, index) => `
        <div class="candidate-card" style="background-color: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div>
                    <h4 style="margin: 0 0 0.5rem 0;">${candidate.name}</h4>
                    <p style="margin: 0; color: #666;">${candidate.institution} ${candidate.country ? `(${candidate.country})` : ''}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: #007bff;">Score: ${candidate.relevance_score.toFixed(1)}</div>
                    <div style="font-size: 0.9em; color: ${candidate.acceptance_status === 'yes' ? 'green' : candidate.acceptance_status === 'no' ? 'red' : '#666'};">
                        ${candidate.acceptance_status === 'yes' ? '✓ Accepting Students' : candidate.acceptance_status === 'no' ? '✗ Not Accepting' : '? Unknown Status'}
                    </div>
                </div>
            </div>

            ${candidate.topics && candidate.topics.length > 0 ? `
                <div style="margin-bottom: 0.5rem;">
                    <strong>Research Areas:</strong> ${candidate.topics.join(', ')}
                </div>
            ` : ''}

            ${candidate.research_description ? `
                <div style="margin-bottom: 0.5rem;">
                    <strong>Research:</strong> ${candidate.research_description.substring(0, 200)}${candidate.research_description.length > 200 ? '...' : ''}
                </div>
            ` : ''}

            ${candidate.personal_homepage ? `
                <div style="margin-top: 0.5rem;">
                    <a href="${candidate.personal_homepage}" target="_blank" style="color: #007bff;">View Profile →</a>
                </div>
            ` : ''}
        </div>
    `).join('');
}
