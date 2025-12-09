
import { renderPcsasTab } from './pcsas';
import { renderAgentsPiFinderTab } from './agents_pi_finder';
import { renderDraftResearchTab } from './draft_research';
import { renderUserProfileTab } from './profile';
import { renderTimeline } from './timeline';
import { renderProgramTracker } from './program_tracker';

/**
 * Renders the initial landing page of the application.
 * @param {HTMLElement} appDiv - The main application div where content will be rendered.
 */
export function renderLandingPage(appDiv: HTMLElement) {
    appDiv.innerHTML = `
        <div class="landing-page">
            <h1>Research Network Hub</h1>
            <p>Welcome to your central hub for academic research tools.</p>

            <h2>Available Tools</h2>
            <div class="tool-list">
                <button class="tool-button" data-tool="user-profile">User Profile</button>
                <button class="tool-button" data-tool="program-discovery">Program Discovery</button>
                <button class="tool-button" data-tool="draft-research">Draft & Research</button>
                <button class="tool-button" data-tool="program-tracker">Program Tracker</button>
            </div>

            <div id="application-timeline-container" style="max-width: 1200px; margin: 2rem auto; padding: 0 2rem;"></div>
        </div>
    `;

    // Render timeline
    const timelineContainer = document.getElementById('application-timeline-container');
    if (timelineContainer) {
        renderTimeline(timelineContainer);
    }

    document.querySelectorAll('.tool-button').forEach(button => {
        button.addEventListener('click', (event) => {
            const tool = (event.target as HTMLElement).dataset.tool;
            if (tool) {
                renderApp(appDiv, tool);
            }
        });
    });
}

/**
 * Renders the main application interface with tabs for different tools.
 * @param {HTMLElement} appDiv - The main application div where content will be rendered.
 * @param {string} initialTab - The ID of the tab to activate initially (e.g., 'search', 'pcsas'). Defaults to 'search'.
 */
export async function renderApp(appDiv: HTMLElement, initialTab: string = 'user-profile') {
    appDiv.innerHTML = `
        <div class="app-header">
            <div class="logo">Research Network</div>
            <div class="tabs">
                <button class="tab-button" data-tab="user-profile">User Profile</button>
                <button class="tab-button" data-tab="program-discovery">Program Discovery</button>
                <button class="tab-button" data-tab="draft-research">Draft & Research</button>
                <button class="tab-button" data-tab="program-tracker">Program Tracker</button>
            </div>
        </div>
        <div class="app-container">
            <div id="tab-content-user-profile" class="tab-content"></div>
            <div id="tab-content-program-discovery" class="tab-content"></div>
            <div id="tab-content-draft-research" class="tab-content"></div>
            <div id="tab-content-program-tracker" class="tab-content"></div>
        </div>
    `;

    const logoElement = document.querySelector('.app-header .logo') as HTMLElement;

    // Make logo clickable to return to hub
    if (logoElement) {
        logoElement.style.cursor = 'pointer';
        logoElement.addEventListener('click', () => {
            renderLandingPage(appDiv);
        });
    }

    // Render tab content
    renderUserProfileTab();
    // renderAgentsPiFinderTab(); // Hidden for now
    renderDraftResearchTab();

    // Render program discovery
    const programDiscoveryContainer = document.getElementById('tab-content-program-discovery');
    if (programDiscoveryContainer) {
        const { renderProgramDiscovery } = await import('./program_discovery');
        renderProgramDiscovery(programDiscoveryContainer);
    }

    // Render program tracker
    const programTrackerContainer = document.getElementById('tab-content-program-tracker');
    if (programTrackerContainer) {
        renderProgramTracker(programTrackerContainer);
    }

    // renderPcsasTab(); // Hidden for now

    // Listen for program discovery open event
    window.addEventListener('open-program-discovery', () => {
        // Switch to program discovery tab
        const tabButton = document.querySelector('[data-tab="program-discovery"]') as HTMLElement;
        if (tabButton) {
            tabButton.click();
        }
    });

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

    // Activate initial tab
    const initialTabButton = document.querySelector(`.tab-button[data-tab="${initialTab}"]`) as HTMLElement;
    if (initialTabButton) {
        initialTabButton.click();
    }

    // Append the modal HTML to the body for displaying author's works
    document.body.insertAdjacentHTML('beforeend', `
        <div id="author-works-modal" class="modal">
            <div class="modal-content">
                <span class="close-button">&times;</span>
                <h3 id="modal-author-name"></h3>
                <p id="modal-author-institution" class="modal-subtitle"></p>
                <div id="modal-works-list"></div>
            </div>
        </div>
    `);

    // Get modal elements
    const modal = document.getElementById('author-works-modal');
    const closeButton = document.querySelector('#author-works-modal .close-button');

    // Close modal when clicking on close button or outside the modal
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            if (modal) modal.style.display = 'none';
        });
    }
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            if (modal) modal.style.display = 'none';
        }
    });
}

/**
 * Displays the author works modal with the given author information and works HTML.
 * @param {string} authorName - The name of the author.
 * @param {string} authorInstitution - The institution of the author.
 * @param {string} worksHtml - The HTML content representing the author's works.
 */
export function showAuthorWorksModal(authorName: string, authorInstitution: string, worksHtml: string) {
    const modal = document.getElementById('author-works-modal');
    const modalAuthorName = document.getElementById('modal-author-name');
    const modalAuthorInstitution = document.getElementById('modal-author-institution');
    const modalWorksList = document.getElementById('modal-works-list');

    if (modal && modalAuthorName && modalAuthorInstitution && modalWorksList) {
        modalAuthorName.textContent = `Works by ${authorName}`;
        modalAuthorInstitution.textContent = authorInstitution;
        modalWorksList.innerHTML = worksHtml;
        modal.style.display = 'flex';
    }
}
