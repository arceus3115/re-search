
import { renderSearchTab } from './search';
import { renderPcsasTab } from './pcsas';
import { renderCrossSearchTab } from './cross_search';

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
                <button class="tool-button" data-tool="search">Academic Paper Search</button>
                <button class="tool-button" data-tool="pcsas">PCSAS</button>
                <button class="tool-button" data-tool="cross-search">Cross-Search Universities</button>
            </div>
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

/**
 * Renders the main application interface with tabs for different tools.
 * @param {HTMLElement} appDiv - The main application div where content will be rendered.
 * @param {string} initialTab - The ID of the tab to activate initially (e.g., 'search', 'pcsas'). Defaults to 'search'.
 */
export async function renderApp(appDiv: HTMLElement, initialTab: string = 'search') {
    appDiv.innerHTML = `
        <div class="app-header">
            <div class="logo">Research Network</div>
            <div class="tabs">
                <button class="tab-button" data-tab="search">Academic Paper Search</button>
                <button class="tab-button" data-tab="pcsas">PCSAS</button>
                <button class="tab-button" data-tab="cross-search">Cross-Search Universities</button>
            </div>
        </div>
        <div class="app-container">
            <div id="tab-content-search" class="tab-content"></div>
            <div id="tab-content-pcsas" class="tab-content"></div>
            <div id="tab-content-cross-search" class="tab-content"></div>
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
    renderSearchTab();
    renderPcsasTab();
    renderCrossSearchTab();

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

    // Append the modal HTML to the body
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
