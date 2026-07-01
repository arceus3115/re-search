/**
 * Profile input form component for collecting user profile data
 */

import { apiUrl } from './config';

export interface UserProfile {
    name: string;
    connected_pis: ConnectedPI[];
    research_interests: string[];
    publications: Publication[];
    presentations: string[];
    program_type: string;
    country_filter?: string;
    cv_accomplishments?: string;
    cv_file_path?: string;
}

export interface ConnectedPI {
    name: string;
    openalex_id?: string;
    institution?: string;
    relationship_type?: string;
    relationship_notes?: string;
    connection_date?: string;
    connection_location?: string;
    h_index?: number;
    research_summary?: string;
    subjects?: string[];
}

export interface Publication {
    title?: string;
    doi?: string;
    url?: string;
    raw?: string;
    authors?: string[];
    publication_year?: number;
    venue?: string;
    abstract?: string;
    citation_count?: number;
    publication_type?: string;
    openalex_id?: string;
    tags?: string[];
}

/**
 * Renders the profile input form
 */
export function renderProfileForm(container: HTMLElement): void {
    container.innerHTML = `
        <div class="agents-container" style="max-width: 1200px; margin: 0 auto; padding: 2rem;">
            <h2 style="margin-bottom: 1.5rem;">Create Your Research Profile</h2>
            <p style="margin-bottom: 2rem; color: #666;">Set up your profile with your research interests, CV, and accomplishments to personalize your emails and statements.</p>

            <div class="agent-form" style="background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 2rem; margin-bottom: 2rem;">
                <h3 style="margin-top: 0;">Profile Information</h3>
                <form id="profile-form">
                <div class="form-group">
                    <label for="profile-name">Your Name *</label>
                    <input type="text" id="profile-name" name="name" required>
                </div>

                <div class="form-group">
                    <label for="program-type">Program Type *</label>
                    <select id="program-type" name="program_type" required>
                        <option value="Clin Psych PhD" selected>Clinical Psychology PhD</option>
                        <option value="Experimental Psych PhD">Experimental Psychology PhD</option>
                        <option value="Cognitive Psych PhD">Cognitive Psychology PhD</option>
                        <option value="Neuroscience PhD">Neuroscience PhD</option>
                        <option value="Other">Other</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="country-filter">Country Filter (Optional)</label>
                    <select id="country-filter" name="country_filter">
                        <option value="">All Countries</option>
                        <option value="US">United States</option>
                        <option value="GB">United Kingdom</option>
                        <option value="CA">Canada</option>
                        <option value="AU">Australia</option>
                        <option value="DE">Germany</option>
                        <option value="FR">France</option>
                        <option value="NL">Netherlands</option>
                        <option value="SE">Sweden</option>
                        <option value="CH">Switzerland</option>
                        <option value="NZ">New Zealand</option>
                    </select>
                    <small>Filter PIs by country (leave blank to search all countries)</small>
                </div>

                <div class="form-group">
                    <label for="research-interests">Research Interests *</label>
                    <textarea id="research-interests" name="research_interests"
                              placeholder="Enter research interests, one per line or comma-separated"
                              rows="4" required></textarea>
                    <small>Separate multiple interests with commas or new lines</small>
                </div>

                <div class="form-group" id="presentations-section" style="display: none;">
                    <label>Presentations (Auto-extracted from CV)</label>
                    <div id="presentations-list" style="background-color: #f8f9fa; padding: 1rem; border-radius: 4px; margin-bottom: 0.5rem;"></div>
                    <small>These presentations were automatically extracted from your CV.</small>
                </div>

                <div class="form-group">
                    <label for="cv-accomplishments">CV / Accomplishments</label>
                    <div class="cv-section">
                        <div class="cv-upload-section" style="margin-bottom: 0.5rem;">
                            <label for="cv-file-upload" class="btn-secondary" style="display: inline-block; cursor: pointer;">
                                Upload CV File (TXT)
                            </label>
                            <input type="file" id="cv-file-upload" accept=".txt" style="display: none;">
                            <span id="cv-file-name" style="margin-left: 10px; color: #666;"></span>
                        </div>
                        <textarea id="cv-accomplishments" name="cv_accomplishments"
                                  placeholder="Or type your CV/accomplishments here (this will be used to personalize your emails and statements)"
                                  rows="8" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; font-family: inherit;"></textarea>
                    </div>
                    <small>You can upload a TXT file or type your accomplishments manually. Uploaded files will have their text extracted automatically.</small>
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn-primary" style="width: 100%; padding: 0.75rem; font-size: 1rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Create Profile</button>
                </div>
            </form>
            </div>

            <!-- Profile Analysis Section -->
            <div id="profile-analysis-section" style="display: none; background-color: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 2rem; margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h3 style="margin-top: 0;">Profile Analysis</h3>
                    <button id="analyze-profile-btn" class="btn-primary" style="padding: 0.75rem 1.5rem; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem;">Analyze Profile</button>
                </div>
                <div id="profile-analysis-results" style="display: none;"></div>
            </div>
        </div>
    `;

    // Add event listeners
    setupProfileFormListeners();

    // Initialize Summernote editors after DOM is ready and jQuery is loaded
    waitForSummernoteAndInitialize();
}

function waitForSummernoteAndInitialize(retries = 10): void {
    if (typeof (window as any).jQuery !== 'undefined' && typeof (window as any).jQuery.fn.summernote !== 'undefined') {
        // jQuery and Summernote are loaded, initialize editors
        setTimeout(() => {
            initializeSummernoteEditors();
        }, 100);
    } else if (retries > 0) {
        // Wait a bit more and try again
        setTimeout(() => {
            waitForSummernoteAndInitialize(retries - 1);
        }, 200);
    } else {
        console.warn('Summernote or jQuery failed to load after multiple attempts');
    }
}

// Store current profile ID for analysis
let currentProfileIdForAnalysis: string | null = null;

function setupProfileFormListeners(): void {
    const form = document.getElementById('profile-form') as HTMLFormElement;
    const cvFileUpload = document.getElementById('cv-file-upload') as HTMLInputElement;
    const analyzeBtn = document.getElementById('analyze-profile-btn');

    if (cvFileUpload) {
        cvFileUpload.addEventListener('change', handleCVUpload);
    }

    if (form) {
        form.addEventListener('submit', handleProfileSubmit);
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleAnalyzeProfile);
    }
}

function initializeSummernoteEditors(): void {
    // Check if jQuery and Summernote are available
    if (typeof (window as any).jQuery === 'undefined' || typeof (window as any).jQuery.fn.summernote === 'undefined') {
        console.warn('Summernote or jQuery not loaded yet');
        return;
    }

    const $ = (window as any).jQuery;

    // Initialize CV/accomplishments editor
    const cvTextarea = document.getElementById('cv-accomplishments');
    if (cvTextarea && !$(cvTextarea).hasClass('summernote-initialized')) {
        $(cvTextarea).summernote({
            height: 300,
            minHeight: 150,
            maxHeight: 400,
            placeholder: 'Or type your CV/accomplishments here (this will be used to personalize your emails and statements)',
            toolbar: [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['fontname', ['fontname']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link']],
                ['view', ['fullscreen', 'codeview', 'help']]
            ]
        });
        $(cvTextarea).addClass('summernote-initialized');
    }

    // Initialize dynamic fields
    initializeSummernoteForDynamicFields();
}

function initializeSummernoteForDynamicFields(): void {
    // Check if jQuery and Summernote are available
    if (typeof (window as any).jQuery === 'undefined' || typeof (window as any).jQuery.fn.summernote === 'undefined') {
        return;
    }

    const $ = (window as any).jQuery;

    // Initialize PI relationship notes
    document.querySelectorAll('.pi-relationship-notes:not(.summernote-initialized)').forEach(textarea => {
        $(textarea).summernote({
            height: 120,
            minHeight: 80,
            maxHeight: 200,
            placeholder: 'Optional notes about the relationship...',
            toolbar: [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['insert', ['link']],
                ['view', ['codeview', 'help']]
            ]
        });
        $(textarea).addClass('summernote-initialized');
    });

    // Initialize publication abstracts
    document.querySelectorAll('.pub-abstract:not(.summernote-initialized)').forEach(textarea => {
        $(textarea).summernote({
            height: 150,
            minHeight: 100,
            maxHeight: 300,
            placeholder: 'Publication abstract...',
            toolbar: [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['insert', ['link']],
                ['view', ['codeview', 'help']]
            ]
        });
        $(textarea).addClass('summernote-initialized');
    });
}

function addPIField(): void {
    const list = document.getElementById('connected-pis-list');
    if (!list) return;

    const piDiv = document.createElement('div');
    piDiv.className = 'pi-entry';
    piDiv.style.cssText = 'background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;';

    const entryId = `pi-entry-${Date.now()}`;
    piDiv.innerHTML = `
        <div class="pi-entry-content">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">PI Name *</label>
                    <input type="text" placeholder="Search by name..." class="pi-name" required
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                    <div class="pi-search-results" style="display: none; position: absolute; background: white; border: 1px solid #ccc; border-radius: 4px; max-height: 200px; overflow-y: auto; z-index: 1000; margin-top: 2px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">OpenAlex ID</label>
                    <input type="text" placeholder="Auto-filled from search" class="pi-openalex-id" readonly
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; background-color: #f5f5f5;">
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Institution</label>
                    <input type="text" placeholder="Auto-filled from search" class="pi-institution" readonly
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; background-color: #f5f5f5;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Relationship Type</label>
                    <select class="pi-relationship-type" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                        <option value="">Select relationship...</option>
                        <option value="mentor">Mentor</option>
                        <option value="collaborator">Collaborator</option>
                        <option value="advisor">Advisor</option>
                        <option value="colleague">Colleague</option>
                        <option value="supervisor">Supervisor</option>
                        <option value="other">Other</option>
                    </select>
                </div>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <label style="font-size: 0.9em; font-weight: 600;">Relationship Notes</label>
                <textarea class="pi-relationship-notes" placeholder="Optional notes about the relationship..."
                          rows="2" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;"></textarea>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Connection Date</label>
                    <input type="text" placeholder="YYYY-MM-DD or free text" class="pi-connection-date"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Connection Location</label>
                    <input type="text" placeholder="Location where you met" class="pi-connection-location"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
            </div>

            <div class="pi-enriched-info" style="display: none; padding: 0.5rem; background: #e8f4f8; border-radius: 4px; margin-bottom: 0.5rem; font-size: 0.9em;">
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;">
                    <div><strong>h-index:</strong> <span class="pi-h-index"></span></div>
                    <div><strong>Subjects:</strong> <span class="pi-subjects"></span></div>
                    <div><strong>Research:</strong> <span class="pi-research-summary" style="font-style: italic; font-size: 0.85em;"></span></div>
                </div>
            </div>

            <button type="button" class="btn-remove" onclick="this.closest('.pi-entry').remove()"
                    style="padding: 0.5rem 1rem; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">Remove</button>
        </div>
    `;
    list.appendChild(piDiv);

    // Add search functionality
    setupPISearch(piDiv);
}

let searchTimeout: NodeJS.Timeout | null = null;

function setupPISearch(piEntry: HTMLElement): void {
    const nameInput = piEntry.querySelector('.pi-name') as HTMLInputElement;
    const openalexInput = piEntry.querySelector('.pi-openalex-id') as HTMLInputElement;
    const institutionInput = piEntry.querySelector('.pi-institution') as HTMLInputElement;
    const resultsDiv = piEntry.querySelector('.pi-search-results') as HTMLElement;
    const enrichedInfo = piEntry.querySelector('.pi-enriched-info') as HTMLElement;
    const hIndexSpan = piEntry.querySelector('.pi-h-index') as HTMLElement;
    const subjectsSpan = piEntry.querySelector('.pi-subjects') as HTMLElement;
    const researchSummarySpan = piEntry.querySelector('.pi-research-summary') as HTMLElement;

    if (!nameInput || !resultsDiv) return;

    nameInput.addEventListener('input', () => {
        const query = nameInput.value.trim();

        if (query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }

        // Debounce search
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        searchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(apiUrl(`/api/v1/profile/pi/search?name=${encodeURIComponent(query)}&limit=5`));
                if (!response.ok) return;

                const data = await response.json();
                const candidates = data.candidates || [];

                if (candidates.length === 0) {
                    resultsDiv.style.display = 'none';
                    return;
                }

                resultsDiv.innerHTML = candidates.map((c: any) => `
                    <div class="pi-search-result" style="padding: 0.5rem; cursor: pointer; border-bottom: 1px solid #eee;"
                         data-openalex-id="${c.openalex_id}" data-name="${c.name}" data-institution="${c.institution || ''}"
                         data-h-index="${c.h_index || 0}" data-subjects="${(c.subjects || []).join(', ')}"
                         onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='white'">
                        <div style="font-weight: 600;">${c.name}</div>
                        ${c.institution ? `<div style="font-size: 0.85em; color: #666;">${c.institution}</div>` : ''}
                        ${c.subjects && c.subjects.length > 0 ? `<div style="font-size: 0.85em; color: #888;">${c.subjects.join(', ')}</div>` : ''}
                        <div style="font-size: 0.85em; color: #888;">h-index: ${c.h_index || 0}</div>
                    </div>
                `).join('');

                resultsDiv.style.display = 'block';

                // Position results div
                const rect = nameInput.getBoundingClientRect();
                resultsDiv.style.position = 'absolute';
                resultsDiv.style.width = `${rect.width}px`;
                resultsDiv.style.left = `${rect.left}px`;
                resultsDiv.style.top = `${rect.bottom}px`;

                // Add click handlers
                resultsDiv.querySelectorAll('.pi-search-result').forEach(result => {
                    result.addEventListener('click', () => {
                        const openalexId = result.getAttribute('data-openalex-id');
                        const name = result.getAttribute('data-name');
                        const institution = result.getAttribute('data-institution');
                        const hIndex = result.getAttribute('data-h-index');
                        const subjects = result.getAttribute('data-subjects');

                        nameInput.value = name || '';
                        if (openalexInput) {
                            openalexInput.value = openalexId || '';
                            openalexInput.removeAttribute('readonly');
                        }
                        if (institutionInput) {
                            institutionInput.value = institution || '';
                            institutionInput.removeAttribute('readonly');
                        }

                        // Show enriched info
                        if (enrichedInfo && hIndexSpan && subjectsSpan) {
                            hIndexSpan.textContent = hIndex || 'N/A';
                            subjectsSpan.textContent = subjects || 'N/A';
                            enrichedInfo.style.display = 'block';
                        }

                        // Fetch full details for research summary
                        if (openalexId) {
                            fetch(apiUrl(`/api/v1/profile/pi/${openalexId}/details`))
                                .then(r => r.json())
                                .then(details => {
                                    if (researchSummarySpan && details.research_summary) {
                                        researchSummarySpan.textContent = details.research_summary.substring(0, 100) + '...';
                                    }
                                })
                                .catch(() => {});
                        }

                        resultsDiv.style.display = 'none';
                    });
                });
            } catch (error) {
                console.error('Error searching for PI:', error);
            }
        }, 300);
    });

    // Hide results when clicking outside
    document.addEventListener('click', (e) => {
        if (!piEntry.contains(e.target as Node)) {
            resultsDiv.style.display = 'none';
        }
    });
}

function addPublicationField(): void {
    const list = document.getElementById('publications-list');
    if (!list) return;

    const pubDiv = document.createElement('div');
    pubDiv.className = 'publication-entry';
    pubDiv.style.cssText = 'background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;';

    pubDiv.innerHTML = `
        <div class="publication-entry-content">
            <div style="margin-bottom: 0.5rem;">
                <label style="font-size: 0.9em; font-weight: 600;">Search Publication</label>
                <input type="text" placeholder="Search by DOI, title, or author..." class="pub-search"
                       style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                <div class="pub-search-results" style="display: none; position: absolute; background: white; border: 1px solid #ccc; border-radius: 4px; max-height: 200px; overflow-y: auto; z-index: 1000; margin-top: 2px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>
            </div>

            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Title</label>
                    <input type="text" placeholder="Auto-filled from search" class="pub-title"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">DOI</label>
                    <input type="text" placeholder="Auto-filled from search" class="pub-doi"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Year</label>
                    <input type="number" placeholder="Year" class="pub-year"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Venue/Journal</label>
                    <input type="text" placeholder="Venue" class="pub-venue"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Type</label>
                    <select class="pub-type" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                        <option value="">Select type...</option>
                        <option value="journal">Journal Article</option>
                        <option value="conference">Conference Paper</option>
                        <option value="preprint">Preprint</option>
                        <option value="book">Book/Chapter</option>
                        <option value="other">Other</option>
                    </select>
                </div>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <label style="font-size: 0.9em; font-weight: 600;">Authors</label>
                <input type="text" placeholder="Comma-separated list of authors" class="pub-authors"
                       style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
            </div>

            <div style="margin-bottom: 0.5rem;">
                <label style="font-size: 0.9em; font-weight: 600;">Abstract</label>
                <textarea class="pub-abstract" placeholder="Publication abstract..." rows="3"
                          style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;"></textarea>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">URL</label>
                    <input type="url" placeholder="Publication URL" class="pub-url"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Citations</label>
                    <input type="number" placeholder="Citation count" class="pub-citations"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
                <div>
                    <label style="font-size: 0.9em; font-weight: 600;">Tags</label>
                    <input type="text" placeholder="Comma-separated tags" class="pub-tags"
                           style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
            </div>

            <div class="pub-enriched-info" style="display: none; padding: 0.5rem; background: #e8f4f8; border-radius: 4px; margin-bottom: 0.5rem; font-size: 0.9em;">
                <div><strong>OpenAlex ID:</strong> <span class="pub-openalex-id"></span></div>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <label style="font-size: 0.9em; font-weight: 600;">Or enter raw text</label>
                <input type="text" placeholder="Raw publication text (if not using search)" class="pub-raw"
                       style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
            </div>

            <button type="button" class="btn-remove" onclick="this.closest('.publication-entry').remove()"
                    style="padding: 0.5rem 1rem; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">Remove</button>
        </div>
    `;
    list.appendChild(pubDiv);

    // Add search functionality
    setupPublicationSearch(pubDiv);
}

let pubSearchTimeout: NodeJS.Timeout | null = null;

function setupPublicationSearch(pubEntry: HTMLElement): void {
    const searchInput = pubEntry.querySelector('.pub-search') as HTMLInputElement;
    const resultsDiv = pubEntry.querySelector('.pub-search-results') as HTMLElement;
    const titleInput = pubEntry.querySelector('.pub-title') as HTMLInputElement;
    const doiInput = pubEntry.querySelector('.pub-doi') as HTMLInputElement;
    const urlInput = pubEntry.querySelector('.pub-url') as HTMLInputElement;
    const authorsInput = pubEntry.querySelector('.pub-authors') as HTMLInputElement;
    const yearInput = pubEntry.querySelector('.pub-year') as HTMLInputElement;
    const venueInput = pubEntry.querySelector('.pub-venue') as HTMLInputElement;
    const abstractInput = pubEntry.querySelector('.pub-abstract') as HTMLTextAreaElement;
    const citationsInput = pubEntry.querySelector('.pub-citations') as HTMLInputElement;
    const typeInput = pubEntry.querySelector('.pub-type') as HTMLSelectElement;
    const enrichedInfo = pubEntry.querySelector('.pub-enriched-info') as HTMLElement;
    const openalexIdSpan = pubEntry.querySelector('.pub-openalex-id') as HTMLElement;

    if (!searchInput || !resultsDiv) return;

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();

        if (query.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }

        // Debounce search
        if (pubSearchTimeout) {
            clearTimeout(pubSearchTimeout);
        }

        pubSearchTimeout = setTimeout(async () => {
            try {
                const response = await fetch(apiUrl(`/api/v1/profile/publication/search?query=${encodeURIComponent(query)}&limit=5`));
                if (!response.ok) return;

                const data = await response.json();
                const publications = data.publications || [];

                if (publications.length === 0) {
                    resultsDiv.style.display = 'none';
                    return;
                }

                resultsDiv.innerHTML = publications.map((p: any) => `
                    <div class="pub-search-result" style="padding: 0.5rem; cursor: pointer; border-bottom: 1px solid #eee;"
                         data-pub-data='${JSON.stringify(p).replace(/'/g, "&#39;")}'
                         onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='white'">
                        <div style="font-weight: 600;">${p.title || 'Untitled'}</div>
                        ${p.authors && p.authors.length > 0 ? `<div style="font-size: 0.85em; color: #666;">${p.authors.slice(0, 3).join(', ')}${p.authors.length > 3 ? '...' : ''}</div>` : ''}
                        ${p.venue ? `<div style="font-size: 0.85em; color: #888;">${p.venue}${p.publication_year ? ` (${p.publication_year})` : ''}</div>` : ''}
                        ${p.citation_count !== undefined ? `<div style="font-size: 0.85em; color: #888;">Citations: ${p.citation_count}</div>` : ''}
                    </div>
                `).join('');

                resultsDiv.style.display = 'block';

                // Position results dropdown below search input
                const rect = searchInput.getBoundingClientRect();
                resultsDiv.style.position = 'absolute';
                resultsDiv.style.width = `${rect.width}px`;
                resultsDiv.style.left = `${rect.left}px`;
                resultsDiv.style.top = `${rect.bottom}px`;

                // Add click handlers for search results
                resultsDiv.querySelectorAll('.pub-search-result').forEach(result => {
                    result.addEventListener('click', () => {
                        const pubDataStr = result.getAttribute('data-pub-data');
                        if (!pubDataStr) return;

                        const pubData = JSON.parse(pubDataStr.replace(/&#39;/g, "'"));

                        // Populate publication fields from search result
                        if (titleInput) titleInput.value = pubData.title || '';
                        if (doiInput) doiInput.value = pubData.doi || '';
                        if (urlInput) urlInput.value = pubData.url || '';
                        if (authorsInput) authorsInput.value = (pubData.authors || []).join(', ');
                        if (yearInput) yearInput.value = pubData.publication_year || '';
                        if (venueInput) venueInput.value = pubData.venue || '';

                        // Set abstract content (handles Summernote initialization if needed)
                        if (abstractInput) {
                            if (typeof (window as any).jQuery !== 'undefined' && (window as any).jQuery.fn.summernote) {
                                const $ = (window as any).jQuery;
                                if ($(abstractInput).hasClass('summernote-initialized')) {
                                    $(abstractInput).summernote('code', pubData.abstract || '');
                                } else {
                                    $(abstractInput).summernote({
                                        height: 150,
                                        minHeight: 100,
                                        maxHeight: 300,
                                        placeholder: 'Publication abstract...',
                                        toolbar: [
                                            ['style', ['style']],
                                            ['font', ['bold', 'italic', 'underline', 'clear']],
                                            ['para', ['ul', 'ol', 'paragraph']],
                                            ['insert', ['link']],
                                            ['view', ['codeview', 'help']]
                                        ]
                                    });
                                    $(abstractInput).addClass('summernote-initialized');
                                    $(abstractInput).summernote('code', pubData.abstract || '');
                                }
                            } else {
                                abstractInput.value = pubData.abstract || '';
                            }
                        }
                        if (citationsInput) citationsInput.value = pubData.citation_count || '';
                        if (typeInput && pubData.publication_type) {
                            const typeValue = pubData.publication_type.toLowerCase().replace(' ', '_');
                            typeInput.value = typeValue;
                        }

                        // Display OpenAlex metadata if available
                        if (enrichedInfo && openalexIdSpan && pubData.openalex_id) {
                            openalexIdSpan.textContent = pubData.openalex_id;
                            enrichedInfo.style.display = 'block';
                        }

                        resultsDiv.style.display = 'none';
                    });
                });
            } catch (error) {
                console.error('Error searching for publication:', error);
            }
        }, 300);
    });

    // Hide results when clicking outside
    document.addEventListener('click', (e) => {
        if (!pubEntry.contains(e.target as Node)) {
            resultsDiv.style.display = 'none';
        }
    });
}

let cvFileData: { text: string; filePath?: string } | null = null;

async function handleCVUpload(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) return;

    const fileNameSpan = document.getElementById('cv-file-name');
    const cvTextArea = document.getElementById('cv-accomplishments') as HTMLTextAreaElement;

    if (fileNameSpan) {
        fileNameSpan.textContent = file.name;
    }

    // Validate file type - only accept .txt files
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    if (fileExt !== 'txt') {
        alert('Unsupported file type. Please upload a TXT file.');
        input.value = '';
        return;
    }

    try {
        // Show loading state
        if (fileNameSpan) {
            fileNameSpan.textContent = `${file.name} (uploading...)`;
        }

        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(apiUrl('/api/v1/profile/cv/upload'), {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            // Try to parse error response for detailed error message
            let errorMessage = 'Failed to upload CV file';
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // If JSON parsing fails, use default message
                console.warn('Could not parse error response:', e);
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();

        // Store extracted text
        cvFileData = {
            text: result.extracted_text || '',
            filePath: result.file_path
        };

        // Update text area with extracted text (Summernote)
        if (cvTextArea) {
            if (typeof (window as any).jQuery !== 'undefined' && (window as any).jQuery.fn.summernote) {
                const $ = (window as any).jQuery;
                // If Summernote is initialized, use its API to set content
                if ($(cvTextArea).hasClass('summernote-initialized')) {
                    $(cvTextArea).summernote('code', result.extracted_text || '');
                } else {
                    // Fallback to plain textarea if not initialized yet
                    cvTextArea.value = result.extracted_text || '';
                }
            } else {
                cvTextArea.value = result.extracted_text || '';
            }
        }

        // Display auto-extracted presentations
        const presentationsSection = document.getElementById('presentations-section');
        const presentationsList = document.getElementById('presentations-list');
        if (presentationsSection && presentationsList && result.presentations && result.presentations.length > 0) {
            presentationsList.innerHTML = result.presentations.map((pres: string) => `
                <div style="padding: 0.5rem; margin-bottom: 0.5rem; background-color: white; border: 1px solid #dee2e6; border-radius: 4px;">
                    ${pres}
                </div>
            `).join('');
            presentationsSection.style.display = 'block';
        } else if (presentationsSection) {
            presentationsSection.style.display = 'none';
        }

        // Store extracted data for profile submission
        (window as any).extractedCVData = {
            presentations: result.presentations || []
        };

        if (fileNameSpan) {
            fileNameSpan.textContent = `${file.name} ✓`;
        }
    } catch (error) {
        console.error('Error uploading CV:', error);
        alert('Failed to upload CV file. Please try again or type your CV manually.');
        if (fileNameSpan) {
            fileNameSpan.textContent = '';
        }
        input.value = '';
    }
}

async function handleProfileSubmit(event: Event): Promise<void> {
    event.preventDefault();
    const form = event.target as HTMLFormElement;

    // Ensure all Summernote editors are synced before collecting data
    // This ensures any unsaved changes are captured
    if (typeof (window as any).jQuery !== 'undefined' && (window as any).jQuery.fn.summernote) {
        const $ = (window as any).jQuery;
        // Trigger blur on all Summernote editors to ensure content is saved
        form.querySelectorAll('.summernote-initialized').forEach((el: Element) => {
            const $el = $(el);
            if ($el.hasClass('summernote-initialized')) {
                // Trigger save by blurring the editor
                $el.summernote('saveRange');
            }
        });
        // Small delay to ensure Summernote has time to sync
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Collect form data
    const countryFilter = (form.querySelector('#country-filter') as HTMLSelectElement).value.trim();
    const cvTextArea = form.querySelector('#cv-accomplishments') as HTMLTextAreaElement;

    // Get CV text from Summernote if initialized, otherwise from textarea
    let cvText = '';
    if (cvTextArea) {
        if (typeof (window as any).jQuery !== 'undefined' && (window as any).jQuery.fn.summernote) {
            const $ = (window as any).jQuery;
            if ($(cvTextArea).hasClass('summernote-initialized')) {
                // Explicitly get the code to ensure we have the latest content
                cvText = $(cvTextArea).summernote('code') || '';
            } else {
                cvText = cvTextArea.value.trim() || '';
            }
        } else {
            cvText = cvTextArea.value.trim() || '';
        }
    }

    // Collect auto-extracted presentations from CV
    const extractedData = (window as any).extractedCVData || { presentations: [] };

    const profile: UserProfile = {
        name: (form.querySelector('#profile-name') as HTMLInputElement).value,
        program_type: (form.querySelector('#program-type') as HTMLSelectElement).value,
        research_interests: parseTextList((form.querySelector('#research-interests') as HTMLTextAreaElement).value),
        connected_pis: [], // Connected PIs functionality removed
        publications: [], // Publications functionality temporarily removed
        presentations: extractedData.presentations || [], // Use auto-extracted presentations from CV
        country_filter: countryFilter || undefined,
        cv_accomplishments: cvText || undefined,
        cv_file_path: cvFileData?.filePath || undefined,
    };

    try {
        // Create profile via API
        const response = await fetch(apiUrl('/api/v1/user_profile'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profile),
        });

        if (!response.ok) {
            throw new Error('Failed to create profile');
        }

        const result = await response.json();
        const profileId = result.profile_id;

        // Store profile ID for analysis
        currentProfileIdForAnalysis = profileId;

        // Show analysis section
        const analysisSection = document.getElementById('profile-analysis-section');
        if (analysisSection) {
            analysisSection.style.display = 'block';
        }

        // Dispatch profile-created event for other components that may listen
        window.dispatchEvent(new CustomEvent('profile-created', { detail: { profileId, profile } }));

        // User stays on profile tab after creation (no redirect)
    } catch (error) {
        console.error('Error creating profile:', error);
        alert('Failed to create profile. Please try again.');
    }
}

function collectPIs(): ConnectedPI[] {
    const pis: ConnectedPI[] = [];
    const entries = document.querySelectorAll('.pi-entry');

    entries.forEach(entry => {
        const name = (entry.querySelector('.pi-name') as HTMLInputElement)?.value.trim();
        if (name) {
            const openalexId = (entry.querySelector('.pi-openalex-id') as HTMLInputElement)?.value.trim();
            const institution = (entry.querySelector('.pi-institution') as HTMLInputElement)?.value.trim();
            const relationshipType = (entry.querySelector('.pi-relationship-type') as HTMLSelectElement)?.value.trim();
            const relationshipNotesEl = entry.querySelector('.pi-relationship-notes') as HTMLTextAreaElement;
            let relationshipNotes = '';
            if (relationshipNotesEl) {
                if (typeof (window as any).jQuery !== 'undefined' && (window as any).jQuery.fn.summernote) {
                    const $ = (window as any).jQuery;
                    if ($(relationshipNotesEl).hasClass('summernote-initialized')) {
                        relationshipNotes = $(relationshipNotesEl).summernote('code') || '';
                    } else {
                        relationshipNotes = relationshipNotesEl.value.trim() || '';
                    }
                } else {
                    relationshipNotes = relationshipNotesEl.value.trim() || '';
                }
            }
            const connectionDate = (entry.querySelector('.pi-connection-date') as HTMLInputElement)?.value.trim();
            const connectionLocation = (entry.querySelector('.pi-connection-location') as HTMLInputElement)?.value.trim();

            // Get enriched info if available
            const hIndexText = (entry.querySelector('.pi-h-index') as HTMLElement)?.textContent;
            const hIndex = hIndexText && hIndexText !== 'N/A' ? parseInt(hIndexText) : undefined;
            const subjectsText = (entry.querySelector('.pi-subjects') as HTMLElement)?.textContent;
            const subjects = subjectsText && subjectsText !== 'N/A' ? subjectsText.split(',').map(s => s.trim()) : undefined;
            const researchSummary = (entry.querySelector('.pi-research-summary') as HTMLElement)?.textContent?.trim();

            pis.push({
                name,
                openalex_id: openalexId || undefined,
                institution: institution || undefined,
                relationship_type: relationshipType || undefined,
                relationship_notes: relationshipNotes || undefined,
                connection_date: connectionDate || undefined,
                connection_location: connectionLocation || undefined,
                h_index: hIndex,
                research_summary: researchSummary || undefined,
                subjects: subjects,
            });
        }
    });

    return pis;
}

function collectPublications(): Publication[] {
    const pubs: Publication[] = [];
    const entries = document.querySelectorAll('.publication-entry');

    entries.forEach(entry => {
        const title = (entry.querySelector('.pub-title') as HTMLInputElement)?.value.trim();
        const doi = (entry.querySelector('.pub-doi') as HTMLInputElement)?.value.trim();
        const url = (entry.querySelector('.pub-url') as HTMLInputElement)?.value.trim();
        const raw = (entry.querySelector('.pub-raw') as HTMLInputElement)?.value.trim();
        const authorsText = (entry.querySelector('.pub-authors') as HTMLInputElement)?.value.trim();
        const authors = authorsText ? authorsText.split(',').map(a => a.trim()) : undefined;
        const yearText = (entry.querySelector('.pub-year') as HTMLInputElement)?.value.trim();
        const year = yearText ? parseInt(yearText) : undefined;
        const venue = (entry.querySelector('.pub-venue') as HTMLInputElement)?.value.trim();
        const abstractEl = entry.querySelector('.pub-abstract') as HTMLTextAreaElement;
        let abstract = '';
        if (abstractEl) {
            if (typeof (window as any).jQuery !== 'undefined' && (window as any).jQuery.fn.summernote) {
                const $ = (window as any).jQuery;
                if ($(abstractEl).hasClass('summernote-initialized')) {
                    abstract = $(abstractEl).summernote('code') || '';
                } else {
                    abstract = abstractEl.value.trim() || '';
                }
            } else {
                abstract = abstractEl.value.trim() || '';
            }
        }
        const citationsText = (entry.querySelector('.pub-citations') as HTMLInputElement)?.value.trim();
        const citations = citationsText ? parseInt(citationsText) : undefined;
        const pubType = (entry.querySelector('.pub-type') as HTMLSelectElement)?.value.trim();
        const tagsText = (entry.querySelector('.pub-tags') as HTMLInputElement)?.value.trim();
        const tags = tagsText ? tagsText.split(',').map(t => t.trim()) : undefined;
        const openalexId = (entry.querySelector('.pub-openalex-id') as HTMLElement)?.textContent?.trim();

        if (title || doi || url || raw || authors || venue) {
            pubs.push({
                title: title || undefined,
                doi: doi || undefined,
                url: url || undefined,
                raw: raw || undefined,
                authors: authors,
                publication_year: year,
                venue: venue || undefined,
                abstract: abstract || undefined,
                citation_count: citations,
                publication_type: pubType || undefined,
                openalex_id: openalexId || undefined,
                tags: tags,
            });
        }
    });

    return pubs;
}

function parseTextList(text: string): string[] {
    if (!text) return [];
    // Split by commas or newlines, trim, and filter empty strings
    return text
        .split(/[,\n]/)
        .map(item => item.trim())
        .filter(item => item.length > 0);
}

async function handleAnalyzeProfile(): Promise<void> {
    if (!currentProfileIdForAnalysis) {
        alert('Please create a profile first');
        return;
    }

    const analyzeBtn = document.getElementById('analyze-profile-btn') as HTMLButtonElement;
    const resultsDiv = document.getElementById('profile-analysis-results');

    if (!analyzeBtn || !resultsDiv) return;

    // Show loading
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
    resultsDiv.style.display = 'none';

    try {
        const response = await fetch(apiUrl('/api/v1/profile/analyze'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile_id: currentProfileIdForAnalysis
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze profile');
        }

        const result = await response.json();

        // Display results
        displayAnalysisResults(result);

    } catch (error: any) {
        console.error('Error analyzing profile:', error);
        alert(`Error: ${error.message}`);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Profile';
    }
}

function displayAnalysisResults(result: any): void {
    const resultsDiv = document.getElementById('profile-analysis-results');
    if (!resultsDiv) return;

    const fitScore = result.fit_score || 0;
    const fitScorePercent = (fitScore * 100).toFixed(0);
    const fitScoreColor = fitScore >= 0.7 ? '#28a745' : fitScore >= 0.5 ? '#ffc107' : '#dc3545';

    const competitiveness = result.competitiveness || 'Moderate';
    const competitivenessColor =
        competitiveness.includes('Highly') ? '#28a745' :
        competitiveness.includes('Competitive') ? '#17a2b8' :
        competitiveness === 'Moderate' ? '#ffc107' : '#dc3545';

    resultsDiv.innerHTML = `
        <div style="background-color: white; border-radius: 6px; padding: 1.5rem;">
            <!-- Overall Fit Score -->
            <div style="margin-bottom: 2rem;">
                <h4 style="margin-top: 0; margin-bottom: 1rem;">Overall Fit Score</h4>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="flex: 1; background-color: #e9ecef; border-radius: 4px; height: 32px; position: relative;">
                        <div style="background-color: ${fitScoreColor}; height: 100%; width: ${fitScorePercent}%; border-radius: 4px; transition: width 0.3s;"></div>
                        <span style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); font-size: 1.1em; font-weight: bold; color: ${fitScore >= 0.5 ? 'white' : '#333'};">
                            ${fitScorePercent}%
                        </span>
                    </div>
                    <span style="padding: 0.5rem 1rem; background-color: ${competitivenessColor}; color: white; border-radius: 4px; font-weight: bold;">
                        ${competitiveness}
                    </span>
                </div>
            </div>

            <!-- Detailed Scores -->
            ${result.detailed_scores && Object.keys(result.detailed_scores).length > 0 ? `
                <div style="margin-bottom: 2rem;">
                    <h4 style="margin-top: 0; margin-bottom: 1rem;">Detailed Scores</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                        ${Object.entries(result.detailed_scores).map(([key, score]: [string, any]) => {
                            const scorePercent = ((score || 0) * 100).toFixed(0);
                            const scoreColor = score >= 0.7 ? '#28a745' : score >= 0.5 ? '#ffc107' : '#dc3545';
                            const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                            return `
                                <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 1rem;">
                                    <div style="font-size: 0.9em; color: #666; margin-bottom: 0.5rem;">${label}</div>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <div style="flex: 1; background-color: #e9ecef; border-radius: 4px; height: 20px; position: relative;">
                                            <div style="background-color: ${scoreColor}; height: 100%; width: ${scorePercent}%; border-radius: 4px;"></div>
                                        </div>
                                        <span style="font-weight: bold; font-size: 0.9em;">${scorePercent}%</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- Strengths -->
            ${result.strengths && result.strengths.length > 0 ? `
                <div style="margin-bottom: 2rem;">
                    <h4 style="margin-top: 0; margin-bottom: 1rem; color: #28a745;">Strengths</h4>
                    <ul style="margin: 0; padding-left: 1.5rem;">
                        ${result.strengths.map((strength: string) => `<li style="margin-bottom: 0.5rem;">${strength}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            <!-- Weaknesses -->
            ${result.weaknesses && result.weaknesses.length > 0 ? `
                <div style="margin-bottom: 2rem;">
                    <h4 style="margin-top: 0; margin-bottom: 1rem; color: #dc3545;">Weaknesses</h4>
                    <ul style="margin: 0; padding-left: 1.5rem;">
                        ${result.weaknesses.map((weakness: string) => `<li style="margin-bottom: 0.5rem;">${weakness}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            <!-- Recommendations -->
            ${result.recommendations && result.recommendations.length > 0 ? `
                <div style="margin-bottom: 2rem;">
                    <h4 style="margin-top: 0; margin-bottom: 1rem; color: #007bff;">Recommendations</h4>
                    <ul style="margin: 0; padding-left: 1.5rem;">
                        ${result.recommendations.map((rec: string) => `<li style="margin-bottom: 0.5rem;">${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            <!-- Gap Analysis -->
            ${result.gap_analysis && (result.gap_analysis.missing_elements?.length > 0 || result.gap_analysis.areas_for_improvement?.length > 0) ? `
                <div style="margin-bottom: 2rem;">
                    <h4 style="margin-top: 0; margin-bottom: 1rem;">Gap Analysis</h4>
                    ${result.gap_analysis.missing_elements && result.gap_analysis.missing_elements.length > 0 ? `
                        <div style="margin-bottom: 1rem;">
                            <strong style="color: #6c757d;">Missing Elements:</strong>
                            <ul style="margin: 0.5rem 0 0 1.5rem; padding-left: 0;">
                                ${result.gap_analysis.missing_elements.map((element: string) => `<li style="margin-bottom: 0.5rem;">${element}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${result.gap_analysis.areas_for_improvement && result.gap_analysis.areas_for_improvement.length > 0 ? `
                        <div>
                            <strong style="color: #6c757d;">Areas for Improvement:</strong>
                            <ul style="margin: 0.5rem 0 0 1.5rem; padding-left: 0;">
                                ${result.gap_analysis.areas_for_improvement.map((area: string) => `<li style="margin-bottom: 0.5rem;">${area}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `;

    resultsDiv.style.display = 'block';
}

/**
 * Renders the User Profile tab
 */
export function renderUserProfileTab(): void {
    const container = document.getElementById('tab-content-user-profile');
    if (!container) return;

    // Render the profile form in the container
    renderProfileForm(container);
}
