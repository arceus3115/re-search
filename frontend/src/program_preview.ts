/**
 * Program Preview Modal Component
 */

import { getProgramResearch } from './api';
import { Program } from './program_discovery';

/**
 * Render program preview modal
 */
export async function renderProgramPreview(container: HTMLElement, program: Program): Promise<void> {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.id = 'program-preview-modal';
    modal.className = 'modal';
    modal.style.display = 'block';

    // Load research data
    let researchData: any = null;
    try {
        const response = await getProgramResearch(program.id);
        researchData = response.research;
    } catch (error) {
        console.error('Error loading research data:', error);
    }

    modal.innerHTML = `
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3>${escapeHtml(program.university_name)}</h3>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                ${renderProgramDetails(program, researchData)}
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="close-preview-btn">Close</button>
                <button class="btn btn-primary" id="add-to-tracker-preview-btn">Add to Tracker</button>
            </div>
        </div>
    `;

    // Append to container or body
    const parent = container.closest('.app-container') || document.body;
    parent.appendChild(modal);

    // Attach event listeners
    attachPreviewListeners(modal, program);
}

/**
 * Render program details
 */
function renderProgramDetails(program: Program, researchData: any): string {
    const accreditationBadges = program.accreditation_sources.map(source =>
        `<span class="accreditation-badge badge-${source.toLowerCase()}">${source}</span>`
    ).join('');

    const fitScore = Math.round((program.fit_score || 0) * 100);
    const fitColor = fitScore >= 70 ? '#28a745' : fitScore >= 50 ? '#ffc107' : '#6c757d';

    let researchSection = '';
    if (researchData) {
        researchSection = renderResearchSection(researchData);
    } else {
        researchSection = '<p>Loading research data...</p>';
    }

    return `
        <div class="program-preview-content">
            <div class="program-preview-basic">
                <h4>Program Information</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>University:</strong> ${escapeHtml(program.university_name)}
                    </div>
                    <div class="info-item">
                        <strong>Program Type:</strong> ${escapeHtml(program.program_type)}
                    </div>
                    <div class="info-item">
                        <strong>Accreditation:</strong> ${accreditationBadges}
                    </div>
                    <div class="info-item">
                        <strong>Fit Score:</strong>
                        <span class="fit-score-badge" style="background-color: ${fitColor};">
                            ${fitScore}%
                        </span>
                    </div>
                    ${program.address ? `
                        <div class="info-item">
                            <strong>Address:</strong> ${escapeHtml(program.address)}
                        </div>
                    ` : ''}
                    ${program.website ? `
                        <div class="info-item">
                            <strong>Website:</strong>
                            <a href="${escapeHtml(program.website)}" target="_blank">${escapeHtml(program.website)}</a>
                        </div>
                    ` : ''}
                    ${program.accreditation_status ? `
                        <div class="info-item">
                            <strong>Status:</strong> ${escapeHtml(program.accreditation_status)}
                        </div>
                    ` : ''}
                </div>

                ${program.score_breakdown ? `
                    <div class="score-breakdown">
                        <h5>Score Breakdown</h5>
                        <div class="breakdown-grid">
                            <div class="breakdown-item">
                                <span class="breakdown-label">Research Interest:</span>
                                <span class="breakdown-value">${Math.round(program.score_breakdown.research_interest * 100)}%</span>
                            </div>
                            <div class="breakdown-item">
                                <span class="breakdown-label">Faculty Match:</span>
                                <span class="breakdown-value">${Math.round(program.score_breakdown.faculty_match * 100)}%</span>
                            </div>
                            <div class="breakdown-item">
                                <span class="breakdown-label">Research Strength:</span>
                                <span class="breakdown-value">${Math.round(program.score_breakdown.research_strength * 100)}%</span>
                            </div>
                            <div class="breakdown-item">
                                <span class="breakdown-label">Geographic:</span>
                                <span class="breakdown-value">${Math.round(program.score_breakdown.geographic * 100)}%</span>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>

            <div class="program-preview-research">
                <h4>Research Strengths</h4>
                ${researchSection}
            </div>
        </div>
    `;
}

/**
 * Render research section
 */
function renderResearchSection(researchData: any): string {
    if (!researchData) {
        return '<p>No research data available.</p>';
    }

    const topTopics = researchData.top_topics || [];
    const topResearchers = researchData.top_researchers || [];
    const recentPapers = researchData.recent_papers || [];

    return `
        ${researchData.research_summary ? `
            <div class="research-summary">
                <p>${escapeHtml(researchData.research_summary)}</p>
            </div>
        ` : ''}

        ${topTopics.length > 0 ? `
            <div class="research-topics">
                <h5>Top Research Topics</h5>
                <div class="topics-list">
                    ${topTopics.map((topic: string) =>
                        `<span class="topic-tag">${escapeHtml(topic)}</span>`
                    ).join('')}
                </div>
            </div>
        ` : ''}

        ${topResearchers.length > 0 ? `
            <div class="research-researchers">
                <h5>Top Researchers (${topResearchers.length})</h5>
                <div class="researchers-list">
                    ${topResearchers.slice(0, 10).map((researcher: any) => `
                        <div class="researcher-item">
                            <div class="researcher-name">
                                ${researcher.homepage_url ?
                                    `<a href="${escapeHtml(researcher.homepage_url)}" target="_blank">${escapeHtml(researcher.name)}</a>` :
                                    escapeHtml(researcher.name)
                                }
                                ${researcher.openalex_id ?
                                    `<a href="${escapeHtml(researcher.openalex_id)}" target="_blank" class="openalex-link">OpenAlex</a>` : ''
                                }
                            </div>
                            <div class="researcher-stats">
                                <span>${researcher.works_count || 0} works</span>
                                ${researcher.total_citations ? `<span>${researcher.total_citations} citations</span>` : ''}
                                ${researcher.h_index ? `<span>h-index: ${researcher.h_index}</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        ${recentPapers.length > 0 ? `
            <div class="research-papers">
                <h5>Recent High-Impact Papers</h5>
                <div class="papers-list">
                    ${recentPapers.slice(0, 10).map((paper: any) => `
                        <div class="paper-item">
                            <div class="paper-title">
                                ${paper.openalex_id ?
                                    `<a href="${escapeHtml(paper.openalex_id)}" target="_blank">${escapeHtml(paper.title || 'Untitled')}</a>` :
                                    escapeHtml(paper.title || 'Untitled')
                                }
                            </div>
                            <div class="paper-meta">
                                ${paper.venue ? `<span class="paper-venue">${escapeHtml(paper.venue)}</span>` : ''}
                                ${paper.publication_year ? `<span class="paper-year">${paper.publication_year}</span>` : ''}
                                ${paper.cited_by_count ? `<span class="paper-citations">${paper.cited_by_count} citations</span>` : ''}
                            </div>
                            ${paper.authors && paper.authors.length > 0 ? `
                                <div class="paper-authors">
                                    ${paper.authors.slice(0, 5).map((author: string) => escapeHtml(author)).join(', ')}
                                    ${paper.authors.length > 5 ? ' et al.' : ''}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

/**
 * Attach event listeners to preview modal
 */
function attachPreviewListeners(modal: HTMLElement, program: Program): void {
    // Close button
    const closeBtn = modal.querySelector('.modal-close');
    const closePreviewBtn = modal.querySelector('#close-preview-btn');

    const closeModal = () => {
        modal.remove();
    };

    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    if (closePreviewBtn) {
        closePreviewBtn.addEventListener('click', closeModal);
    }

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Add to tracker button
    const addToTrackerBtn = modal.querySelector('#add-to-tracker-preview-btn');
    if (addToTrackerBtn) {
        addToTrackerBtn.addEventListener('click', () => {
            addToTracker(program);
            closeModal();
        });
    }
}

/**
 * Add program to tracker
 */
function addToTracker(program: Program): void {
    window.dispatchEvent(new CustomEvent('add-program-to-tracker', {
        detail: {
            name: program.program_type,
            institution: program.university_name,
            status: 'interested',
            notes: program.research_summary || ''
        }
    }));

    window.dispatchEvent(new CustomEvent('open-program-tracker'));
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
