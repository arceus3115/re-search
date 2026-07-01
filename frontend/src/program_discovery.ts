/**
 * Program Discovery Component for finding and ranking clinical psychology programs
 */

import { discoverPrograms, getProgramStats } from './api';
import { apiUrl } from './config';
import { renderProgramPreview } from './program_preview';

export interface Program {
    id: string;
    university_name: string;
    program_type: string;
    accreditation_sources: string[];
    address?: string;
    website?: string;
    accreditation_status: string;
    fit_score: number;
    score_breakdown?: {
        research_interest: number;
        faculty_match: number;
        research_strength: number;
        geographic: number;
    };
    top_topics?: string[];
    top_researchers?: string[];  // Researcher names
    top_researchers_count?: number;
    top_papers?: Array<{
        title: string;
        url?: string;
        doi?: string;
        openalex_id?: string;
        publication_year?: number;
        cited_by_count?: number;
    }>;
    research_summary?: string;
}

/**
 * Render the program discovery component
 */
export function renderProgramDiscovery(container: HTMLElement): void {
    container.innerHTML = `
        <div class="program-discovery-container">
            <div class="program-discovery-header">
                <h2>Program Discovery</h2>
                <p class="program-discovery-subtitle">Find clinical psychology programs ranked by research fit</p>
            </div>

            <div class="program-discovery-controls">
                <div class="discovery-actions">
                    <button id="load-programs-btn" class="btn btn-primary">Load Programs</button>
                    <button id="refresh-programs-btn" class="btn btn-secondary">Refresh Data</button>
                </div>
                <div class="search-filters">
                    <div class="form-group" style="margin-bottom: 0;">
                        <input type="text" id="program-search" placeholder="Search programs..."
                               style="width: 100%; padding: var(--spacing-xs) var(--spacing-sm);
                                      border: 1px solid var(--color-gray-light);
                                      border-radius: var(--border-radius-sm);
                                      font-size: 1em; margin-bottom: 0;">
                    </div>
                    <div class="form-group" style="margin-bottom: 0; display: flex; align-items: center; gap: var(--spacing-sm);">
                        <label for="fit-score-filter" style="margin-bottom: 0; white-space: nowrap;">
                            Min Fit Score: <span id="fit-score-value">0%</span>
                        </label>
                        <input type="range" id="fit-score-filter" min="0" max="100" value="0"
                               style="flex: 1; max-width: 200px;">
                    </div>
                </div>
            </div>

            <div id="program-stats" class="program-stats" style="display: none; margin-bottom: var(--spacing-lg);"></div>

            <div id="programs-loading" class="loading-state" style="display: none; text-align: center; padding: var(--spacing-xl);">
                <p>Loading programs...</p>
            </div>

            <div id="programs-container" class="programs-container">
                <div class="empty-state">
                    <p>Click "Load Programs" to discover programs ranked by your research interests.</p>
                </div>
            </div>

            <div id="program-pagination" class="pagination" style="display: none; margin-top: var(--spacing-lg);"></div>
        </div>
    `;

    attachEventListeners(container);
}

/**
 * Attach event listeners
 */
function attachEventListeners(container: HTMLElement): void {
    const loadBtn = container.querySelector('#load-programs-btn');
    const refreshBtn = container.querySelector('#refresh-programs-btn');
    const searchInput = container.querySelector('#program-search') as HTMLInputElement;
    const fitScoreSlider = container.querySelector('#fit-score-filter') as HTMLInputElement;
    const fitScoreValue = container.querySelector('#fit-score-value');

    let currentPrograms: Program[] = [];
    let currentPage = 1;
    let currentMinFitScore = 0.0;

    // Load programs button
    if (loadBtn) {
        loadBtn.addEventListener('click', async () => {
            await loadPrograms(container, 1, currentMinFitScore);
        });
    }

    // Refresh button
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            if (confirm('This will refresh all program data. This may take a few minutes. Continue?')) {
                try {
                    const response = await fetch(apiUrl('/api/v1/programs/refresh'), { method: 'POST' });
                    if (response.ok) {
                        alert('Program data refreshed successfully!');
                        await loadPrograms(container, 1, currentMinFitScore);
                    } else {
                        alert('Failed to refresh program data.');
                    }
                } catch (error) {
                    console.error('Error refreshing programs:', error);
                    alert('Error refreshing program data.');
                }
            }
        });
    }

    // Fit score slider
    if (fitScoreSlider && fitScoreValue) {
        fitScoreSlider.addEventListener('input', (e) => {
            const value = parseInt((e.target as HTMLInputElement).value);
            fitScoreValue.textContent = `${value}%`;
            currentMinFitScore = value / 100;
        });

        fitScoreSlider.addEventListener('change', () => {
            loadPrograms(container, 1, currentMinFitScore);
        });
    }

    // Search input
    if (searchInput) {
        let searchTimeout: NodeJS.Timeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = (e.target as HTMLInputElement).value.toLowerCase();

            searchTimeout = setTimeout(() => {
                filterPrograms(container, currentPrograms, query);
            }, 300);
        });
    }

    // Programs are only loaded when user clicks "Load Programs" button
    // No auto-loading on initial render
}

/**
 * Load programs from API
 */
async function loadPrograms(container: HTMLElement, page: number, minFitScore: number): Promise<void> {
    const loadingEl = container.querySelector('#programs-loading') as HTMLElement;
    const programsContainer = container.querySelector('#programs-container') as HTMLElement;
    const paginationEl = container.querySelector('#program-pagination') as HTMLElement;
    const statsEl = container.querySelector('#program-stats') as HTMLElement;

    if (loadingEl) loadingEl.style.display = 'block';
    if (programsContainer) programsContainer.innerHTML = '';

    try {
        // Load stats
        try {
            const stats = await getProgramStats();
            if (statsEl) {
                (statsEl as HTMLElement).innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-label">Total Programs:</span>
                            <span class="stat-value">${stats.total_programs}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">APA Accredited:</span>
                            <span class="stat-value">${stats.apa_accredited}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">PCSAS Accredited:</span>
                            <span class="stat-value">${stats.pcsas_accredited}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Both:</span>
                            <span class="stat-value">${stats.both_accredited}</span>
                        </div>
                    </div>
                `;
                (statsEl as HTMLElement).style.display = 'block';
            }
        } catch (error) {
            console.warn('Failed to load stats:', error);
        }

        // Load programs
        const response = await getProgramsData(page, minFitScore);
        const programs: Program[] = response.programs || [];
        const pagination = response.pagination || {};

        if (programsContainer) {
            if (programs.length === 0) {
                (programsContainer as HTMLElement).innerHTML = `
                    <div class="empty-state">
                        <p>No programs found matching your criteria.</p>
                    </div>
                `;
            } else {
                (programsContainer as HTMLElement).innerHTML = renderProgramsList(programs);
                attachProgramListeners(container, programs);
            }
        }

        // Render pagination
        if (paginationEl && pagination.total_pages > 1) {
            (paginationEl as HTMLElement).innerHTML = renderPagination(pagination, page, (newPage: number) => {
                loadPrograms(container, newPage, minFitScore);
            });
            (paginationEl as HTMLElement).style.display = 'block';
        } else if (paginationEl) {
            (paginationEl as HTMLElement).style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading programs:', error);
        if (programsContainer) {
            // Check if it's a 404 error (no user profile)
            // Check both status property and error message to be safe
            const errorStatus = (error as any)?.status;
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            const is404 = errorStatus === 404 || errorMessage.includes('404') || errorMessage.includes('Not Found');

            if (is404) {
                // Show helpful message for 404 (no user profile) - don't leak backend error details
                (programsContainer as HTMLElement).innerHTML = `
                    <div class="error-state">
                        <p><strong>No user profile found.</strong></p>
                        <p>Please create a profile in the 'User Profile' tab first, then click 'Load Programs' to discover programs ranked by your research interests.</p>
                    </div>
                `;
            } else {
                // Show generic error for other errors - don't show backend error details
                (programsContainer as HTMLElement).innerHTML = `
                    <div class="error-state">
                        <p>Error loading programs. Please try again.</p>
                        <p>If the problem persists, please check your connection and try again later.</p>
                    </div>
                `;
            }
        }
    } finally {
        if (loadingEl) (loadingEl as HTMLElement).style.display = 'none';
    }
}

/**
 * Get programs data (wrapper for API call)
 */
async function getProgramsData(page: number, minFitScore: number): Promise<any> {
    return await discoverPrograms(page, 25, minFitScore);
}

/**
 * Filter programs by search query
 */
function filterPrograms(container: HTMLElement, programs: Program[], query: string): void {
    const programsContainer = container.querySelector('#programs-container');
    if (!programsContainer) return;

    if (!query) {
        programsContainer.innerHTML = renderProgramsList(programs);
        attachProgramListeners(container, programs);
        return;
    }

    const filtered = programs.filter(p =>
        p.university_name.toLowerCase().includes(query) ||
        p.address?.toLowerCase().includes(query) ||
        p.top_topics?.some(topic => topic.toLowerCase().includes(query))
    );

    programsContainer.innerHTML = renderProgramsList(filtered);
    attachProgramListeners(container, filtered);
}

/**
 * Render programs list
 */
function renderProgramsList(programs: Program[]): string {
    if (programs.length === 0) {
        return '<div class="empty-state"><p>No programs found.</p></div>';
    }

    return `
        <div class="programs-grid">
            ${programs.map(program => renderProgramCard(program)).join('')}
        </div>
    `;
}

/**
 * Render a single program card
 */
function renderProgramCard(program: Program): string {
    const fitScore = Math.round((program.fit_score || 0) * 100);
    const fitColor = fitScore >= 70 ? '#28a745' : fitScore >= 50 ? '#ffc107' : '#6c757d';

    const accreditationBadges = program.accreditation_sources.map(source =>
        `<span class="accreditation-badge badge-${source.toLowerCase()}">${source}</span>`
    ).join('');

    return `
        <div class="program-card" data-program-id="${program.id}">
            <div class="program-card-header">
                <h3 class="program-card-title">${escapeHtml(program.university_name)}</h3>
                <div class="program-card-badges">
                    ${accreditationBadges}
                    <span class="fit-score-badge" style="background-color: ${fitColor};">
                        ${fitScore}% Fit
                    </span>
                </div>
            </div>
            <div class="program-card-body">
                <p class="program-type"><strong>Program:</strong> ${escapeHtml(program.program_type)}</p>
                ${program.address ? `<p class="program-address"><strong>Location:</strong> ${escapeHtml(program.address)}</p>` : ''}
                ${program.research_summary ? `<p class="program-research-summary">${formatResearchSummary(program.research_summary, program.top_papers || [])}</p>` : ''}
                ${program.top_topics && program.top_topics.length > 0 ?
                    `<p class="program-topics"><strong>Research Areas:</strong> ${program.top_topics.map(t => escapeHtml(t)).join(', ')}</p>` : ''}
                ${program.top_researchers && program.top_researchers.length > 0 ?
                    `<p class="program-researchers"><strong>Top Researchers:</strong> ${program.top_researchers.map(name => escapeHtml(name)).join(', ')}</p>` : ''}
            </div>
            <div class="program-card-actions">
                <button class="btn btn-sm btn-primary view-research-btn" data-program-id="${program.id}">View Research</button>
                <button class="btn btn-sm btn-success add-to-tracker-btn" data-program-id="${program.id}">Add to Tracker</button>
            </div>
        </div>
    `;
}

/**
 * Attach listeners to program cards
 */
function attachProgramListeners(container: HTMLElement, programs: Program[]): void {
    // View research buttons
    container.querySelectorAll('.view-research-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const programId = (e.target as HTMLElement).getAttribute('data-program-id');
            if (programId) {
                const program = programs.find(p => p.id === programId);
                if (program) {
                    await showProgramPreview(container, program);
                }
            }
        });
    });

    // Add to tracker buttons
    container.querySelectorAll('.add-to-tracker-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const programId = (e.target as HTMLElement).getAttribute('data-program-id');
            if (programId) {
                const program = programs.find(p => p.id === programId);
                if (program) {
                    addToTracker(program);
                }
            }
        });
    });
}

/**
 * Show program preview modal
 */
async function showProgramPreview(container: HTMLElement, program: Program): Promise<void> {
    await renderProgramPreview(container, program);
}

/**
 * Add program to tracker
 */
function addToTracker(program: Program): void {
    // Dispatch event to open program tracker with pre-filled data
    window.dispatchEvent(new CustomEvent('add-program-to-tracker', {
        detail: {
            name: program.program_type,
            institution: program.university_name,
            status: 'interested',
            notes: program.research_summary || ''
        }
    }));

    // Switch to program tracker tab
    window.dispatchEvent(new CustomEvent('open-program-tracker'));
}

/**
 * Render pagination
 */
function renderPagination(pagination: any, currentPage: number, onPageChange: (page: number) => void): string {
    const pages = [];
    const totalPages = pagination.total_pages || 1;

    // Previous button
    pages.push(`
        <button class="pagination-btn ${!pagination.has_previous ? 'disabled' : ''}"
                ${!pagination.has_previous ? 'disabled' : ''}
                data-page="${currentPage - 1}">Previous</button>
    `);

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            pages.push(`
                <button class="pagination-btn ${i === currentPage ? 'active' : ''}"
                        data-page="${i}">${i}</button>
            `);
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            pages.push('<span class="pagination-ellipsis">...</span>');
        }
    }

    // Next button
    pages.push(`
        <button class="pagination-btn ${!pagination.has_next ? 'disabled' : ''}"
                ${!pagination.has_next ? 'disabled' : ''}
                data-page="${currentPage + 1}">Next</button>
    `);

    const paginationHtml = pages.join('');

    // Attach event listeners after a short delay to ensure DOM is ready
    setTimeout(() => {
        document.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt((e.target as HTMLElement).getAttribute('data-page') || '1');
                if (page && !(e.target as HTMLElement).classList.contains('disabled')) {
                    onPageChange(page);
                }
            });
        });
    }, 100);

    return paginationHtml;
}

/**
 * Format research summary with clickable paper links
 * Returns HTML string (not escaped) since we're inserting links
 */
function formatResearchSummary(summary: string, papers: Array<{title: string; url?: string; doi?: string; openalex_id?: string}>): string {
    if (!papers || papers.length === 0) {
        return escapeHtml(summary);
    }

    // Split summary into parts and process "Key papers:" section separately
    // Format: "Found X papers. Top researchers: Names. Key papers: Title1: summary1 | Title2: summary2"
    const parts = summary.split('Key papers:');

    if (parts.length === 2) {
        // Process the part before "Key papers:"
        const beforePapers = escapeHtml(parts[0].trim());

        // Process the papers section
        const papersSection = parts[1].trim();
        const paperEntries = papersSection.split('|');
        const formattedPaperEntries: string[] = [];

        // For each paper entry (format: "Title: summary")
        for (const entry of paperEntries) {
            const trimmedEntry = entry.trim();
            if (!trimmedEntry) continue;

            // Try to match with a paper from our list
            // Split entry into title and summary first
            const colonIndex = trimmedEntry.indexOf(':');
            if (colonIndex > 0) {
                const entryTitle = trimmedEntry.substring(0, colonIndex).trim();
                const entrySummary = trimmedEntry.substring(colonIndex + 1).trim();

                let matched = false;
                for (const paper of papers) {
                    if (paper.title) {
                        // Match on title prefix (case-insensitive)
                        // Compare first 50-60 characters to handle truncation
                        const titlePrefix = paper.title.substring(0, Math.min(60, paper.title.length)).toLowerCase();
                        const entryPrefix = entryTitle.substring(0, Math.min(60, entryTitle.length)).toLowerCase();

                        if (entryPrefix === titlePrefix || entryTitle.toLowerCase().startsWith(titlePrefix) || titlePrefix.startsWith(entryPrefix)) {
                            // Get URL
                            let paperUrl = paper.url;
                            if (!paperUrl && paper.doi) {
                                const doi = paper.doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '');
                                paperUrl = `https://doi.org/${doi}`;
                            }
                            if (!paperUrl && paper.openalex_id) {
                                paperUrl = paper.openalex_id;
                            }

                            if (paperUrl) {
                                const title = escapeHtml(entryTitle);
                                const summary = escapeHtml(entrySummary);
                                const link = `<a href="${escapeHtml(paperUrl)}" target="_blank" class="paper-link">${title}</a>`;
                                formattedPaperEntries.push(`${link}: ${summary}`);
                                matched = true;
                                break;
                            }
                        }
                    }
                }

                // If no match, just escape the entry
                if (!matched) {
                    formattedPaperEntries.push(escapeHtml(trimmedEntry));
                }
            } else {
                // No colon found, just escape the entry
                formattedPaperEntries.push(escapeHtml(trimmedEntry));
            }
        }

        return `${beforePapers} Key papers: ${formattedPaperEntries.join(' | ')}`;
    }

    // If no "Key papers:" section, just escape the whole summary
    return escapeHtml(summary);
}

/**
 * Utility: Escape regex special characters
 */
function escapeRegex(text: string): string {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
