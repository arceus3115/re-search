/**
 * Program Tracker Component for tracking graduate school applications
 */

export interface Program {
    id: string;
    name: string;
    institution: string;
    advisor?: string;
    status: 'interested' | 'applied' | 'interview' | 'accepted' | 'rejected' | 'waitlisted';
    applicationDeadline?: string;
    interviewDate?: string;
    decisionDate?: string;
    notes?: string;
}

const STORAGE_KEY = 'program-tracker-programs';

/**
 * Load programs from localStorage
 */
function loadPrograms(): Program[] {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            return JSON.parse(stored) as Program[];
        }
    } catch (e) {
        console.warn('Failed to load programs from localStorage:', e);
    }
    return [];
}

/**
 * Save programs to localStorage
 */
function savePrograms(programs: Program[]): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(programs));
    } catch (e) {
        console.warn('Failed to save programs to localStorage:', e);
    }
}

/**
 * Generate a unique ID for a program
 */
function generateProgramId(): string {
    return `program-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Render the program tracker component
 */
export function renderProgramTracker(container: HTMLElement): void {
    const programs = loadPrograms();
    const statusFilter = getCurrentStatusFilter();

    container.innerHTML = `
        <div class="program-tracker-container">
            <div class="program-tracker-header">
                <h2>Program Tracker</h2>
                <p class="program-tracker-subtitle">Track your applications through interviews to decisions</p>
            </div>

            <div class="program-tracker-controls">
                <div class="tracker-actions">
                    <button id="add-program-btn" class="btn btn-primary">+ Add Program</button>
                    <button id="discover-programs-btn" class="btn btn-secondary">Discover Programs</button>
                </div>
                <div class="status-filters">
                    <button class="filter-btn ${statusFilter === 'all' ? 'active' : ''}" data-filter="all">All</button>
                    <button class="filter-btn ${statusFilter === 'interested' ? 'active' : ''}" data-filter="interested">Interested</button>
                    <button class="filter-btn ${statusFilter === 'applied' ? 'active' : ''}" data-filter="applied">Applied</button>
                    <button class="filter-btn ${statusFilter === 'interview' ? 'active' : ''}" data-filter="interview">Interview</button>
                    <button class="filter-btn ${statusFilter === 'accepted' ? 'active' : ''}" data-filter="accepted">Accepted</button>
                    <button class="filter-btn ${statusFilter === 'rejected' ? 'active' : ''}" data-filter="rejected">Rejected</button>
                    <button class="filter-btn ${statusFilter === 'waitlisted' ? 'active' : ''}" data-filter="waitlisted">Waitlisted</button>
                </div>
            </div>

            <div id="programs-container" class="programs-container">
                ${renderProgramsList(programs, statusFilter)}
            </div>
        </div>

        <!-- Program Form Modal -->
        <div id="program-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 id="modal-title">Add Program</h3>
                    <span class="modal-close">&times;</span>
                </div>
                <form id="program-form" class="program-form">
                    <input type="hidden" id="program-id" name="id">

                    <div class="form-group">
                        <label for="program-name">Program Name *</label>
                        <input type="text" id="program-name" name="name" required placeholder="e.g., Clinical Psychology PhD">
                    </div>

                    <div class="form-group">
                        <label for="program-institution">Institution *</label>
                        <input type="text" id="program-institution" name="institution" required placeholder="e.g., University of California, Berkeley">
                    </div>

                    <div class="form-group">
                        <label for="program-advisor">Advisor (optional)</label>
                        <input type="text" id="program-advisor" name="advisor" placeholder="e.g., Dr. Jane Smith">
                    </div>

                    <div class="form-group">
                        <label for="program-status">Status *</label>
                        <select id="program-status" name="status" required>
                            <option value="interested">Interested</option>
                            <option value="applied">Applied</option>
                            <option value="interview">Interview</option>
                            <option value="accepted">Accepted</option>
                            <option value="rejected">Rejected</option>
                            <option value="waitlisted">Waitlisted</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="program-application-deadline">Application Deadline</label>
                        <input type="date" id="program-application-deadline" name="applicationDeadline">
                    </div>

                    <div class="form-group">
                        <label for="program-interview-date">Interview Date</label>
                        <input type="date" id="program-interview-date" name="interviewDate">
                    </div>

                    <div class="form-group">
                        <label for="program-decision-date">Decision Date</label>
                        <input type="date" id="program-decision-date" name="decisionDate">
                    </div>

                    <div class="form-group">
                        <label for="program-notes">Notes</label>
                        <textarea id="program-notes" name="notes" rows="4" placeholder="Additional notes about this program..."></textarea>
                    </div>

                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" id="cancel-program-btn">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Program</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // Attach event listeners
    attachEventListeners(container);
}

/**
 * Render the programs list
 */
function renderProgramsList(programs: Program[], statusFilter: string): string {
    const filteredPrograms = statusFilter === 'all'
        ? programs
        : programs.filter(p => p.status === statusFilter);

    if (filteredPrograms.length === 0) {
        return `
            <div class="empty-state">
                <p>No programs found. Click "Add Program" to get started!</p>
            </div>
        `;
    }

    return `
        <div class="programs-grid">
            ${filteredPrograms.map(program => renderProgramCard(program)).join('')}
        </div>
    `;
}

/**
 * Render a single program card
 */
function renderProgramCard(program: Program): string {
    const statusColors: { [key: string]: string } = {
        'interested': '#6c757d',
        'applied': '#007bff',
        'interview': '#ffc107',
        'accepted': '#28a745',
        'rejected': '#dc3545',
        'waitlisted': '#fd7e14'
    };

    const statusLabels: { [key: string]: string } = {
        'interested': 'Interested',
        'applied': 'Applied',
        'interview': 'Interview',
        'accepted': 'Accepted',
        'rejected': 'Rejected',
        'waitlisted': 'Waitlisted'
    };

    const color = statusColors[program.status] || '#6c757d';

    return `
        <div class="program-card" data-program-id="${program.id}">
            <div class="program-card-header">
                <h3 class="program-card-title">${escapeHtml(program.name)}</h3>
                <span class="program-status-badge" style="background-color: ${color};">
                    ${statusLabels[program.status]}
                </span>
            </div>
            <div class="program-card-body">
                <p class="program-institution"><strong>Institution:</strong> ${escapeHtml(program.institution)}</p>
                ${program.advisor ? `<p class="program-advisor"><strong>Advisor:</strong> ${escapeHtml(program.advisor)}</p>` : ''}
                ${program.applicationDeadline ? `<p class="program-deadline"><strong>Application Deadline:</strong> ${formatDate(program.applicationDeadline)}</p>` : ''}
                ${program.interviewDate ? `<p class="program-interview"><strong>Interview Date:</strong> ${formatDate(program.interviewDate)}</p>` : ''}
                ${program.decisionDate ? `<p class="program-decision"><strong>Decision Date:</strong> ${formatDate(program.decisionDate)}</p>` : ''}
                ${program.notes ? `<p class="program-notes">${escapeHtml(program.notes)}</p>` : ''}
            </div>
            <div class="program-card-actions">
                <button class="btn btn-sm btn-primary edit-program-btn" data-program-id="${program.id}">Edit</button>
                <button class="btn btn-sm btn-danger delete-program-btn" data-program-id="${program.id}">Delete</button>
            </div>
        </div>
    `;
}

/**
 * Attach event listeners
 */
function attachEventListeners(container: HTMLElement): void {
    // Add program button
    const addBtn = container.querySelector('#add-program-btn');
    if (addBtn) {
        addBtn.addEventListener('click', () => openProgramModal(container));
    }

    // Discover programs button
    const discoverBtn = container.querySelector('#discover-programs-btn');
    if (discoverBtn) {
        discoverBtn.addEventListener('click', () => {
            // Switch to program discovery view
            window.dispatchEvent(new CustomEvent('open-program-discovery'));
        });
    }

    // Listen for add-program-to-tracker event
    window.addEventListener('add-program-to-tracker', ((e: CustomEvent) => {
        const programData = e.detail;
        if (programData) {
            // Directly add the program to the tracker without opening modal
            const program: Program = {
                id: generateProgramId(),
                name: programData.name || '',
                institution: programData.institution || '',
                advisor: programData.advisor || undefined,
                status: (programData.status || 'interested') as Program['status'],
                applicationDeadline: programData.applicationDeadline || undefined,
                interviewDate: programData.interviewDate || undefined,
                decisionDate: programData.decisionDate || undefined,
                notes: programData.notes || undefined,
            };

            const programs = loadPrograms();
            programs.push(program);
            savePrograms(programs);

            // Refresh the programs list
            const statusFilter = getCurrentStatusFilter();
            const programsContainer = container.querySelector('#programs-container');
            if (programsContainer) {
                programsContainer.innerHTML = renderProgramsList(programs, statusFilter);
                attachEditDeleteListeners(container);
            }

            // Show success feedback
            alert(`Added "${program.name}" to your tracker!`);
        }
    }) as EventListener);

    // Filter buttons
    container.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = (e.target as HTMLElement).getAttribute('data-filter');
            if (filter) {
                setStatusFilter(filter);
                const programs = loadPrograms();
                const programsContainer = container.querySelector('#programs-container');
                if (programsContainer) {
                    programsContainer.innerHTML = renderProgramsList(programs, filter);
                }
                // Re-attach event listeners for edit/delete buttons
                attachEditDeleteListeners(container);
                // Update filter button active states
                container.querySelectorAll('.filter-btn').forEach(b => {
                    b.classList.remove('active');
                });
                (e.target as HTMLElement).classList.add('active');
            }
        });
    });

    // Form submission
    const form = container.querySelector('#program-form') as HTMLFormElement;
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            handleProgramSubmit(container);
        });
    }

    // Cancel button
    const cancelBtn = container.querySelector('#cancel-program-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => closeProgramModal(container));
    }

    // Modal close button
    const closeBtn = container.querySelector('.modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => closeProgramModal(container));
    }

    // Close modal when clicking outside
    const modal = container.querySelector('#program-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeProgramModal(container);
            }
        });
    }

    // Attach edit/delete listeners
    attachEditDeleteListeners(container);
}

/**
 * Attach edit and delete button listeners
 */
function attachEditDeleteListeners(container: HTMLElement): void {
    // Edit buttons
    container.querySelectorAll('.edit-program-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const programId = (e.target as HTMLElement).getAttribute('data-program-id');
            if (programId) {
                openProgramModal(container, programId);
            }
        });
    });

    // Delete buttons
    container.querySelectorAll('.delete-program-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const programId = (e.target as HTMLElement).getAttribute('data-program-id');
            if (programId && confirm('Are you sure you want to delete this program?')) {
                deleteProgram(container, programId);
            }
        });
    });
}

/**
 * Open program modal
 */
function openProgramModal(container?: HTMLElement, programId?: string): void {
    const modal = (container || document).querySelector('#program-modal') as HTMLElement;
    const form = (container || document).querySelector('#program-form') as HTMLFormElement;
    const modalTitle = (container || document).querySelector('#modal-title');

    if (!modal || !form) return;

    if (programId) {
        // Edit mode
        const programs = loadPrograms();
        const program = programs.find(p => p.id === programId);
        if (program) {
            if (modalTitle) modalTitle.textContent = 'Edit Program';
            populateForm(form, program);
        }
    } else {
        // Add mode
        if (modalTitle) modalTitle.textContent = 'Add Program';
        form.reset();
        (form.querySelector('#program-id') as HTMLInputElement).value = '';
    }

    modal.style.display = 'block';
}

/**
 * Close program modal
 */
function closeProgramModal(container: HTMLElement): void {
    const modal = container.querySelector('#program-modal') as HTMLElement;
    const form = container.querySelector('#program-form') as HTMLFormElement;

    if (modal) modal.style.display = 'none';
    if (form) form.reset();
}

/**
 * Populate form with program data
 */
function populateForm(form: HTMLFormElement, program: Program): void {
    (form.querySelector('#program-id') as HTMLInputElement).value = program.id;
    (form.querySelector('#program-name') as HTMLInputElement).value = program.name;
    (form.querySelector('#program-institution') as HTMLInputElement).value = program.institution;
    (form.querySelector('#program-advisor') as HTMLInputElement).value = program.advisor || '';
    (form.querySelector('#program-status') as HTMLSelectElement).value = program.status;
    (form.querySelector('#program-application-deadline') as HTMLInputElement).value = program.applicationDeadline || '';
    (form.querySelector('#program-interview-date') as HTMLInputElement).value = program.interviewDate || '';
    (form.querySelector('#program-decision-date') as HTMLInputElement).value = program.decisionDate || '';
    (form.querySelector('#program-notes') as HTMLTextAreaElement).value = program.notes || '';
}

/**
 * Handle program form submission
 */
function handleProgramSubmit(container: HTMLElement): void {
    const form = container.querySelector('#program-form') as HTMLFormElement;
    if (!form) return;

    const formData = new FormData(form);
    const programId = (form.querySelector('#program-id') as HTMLInputElement).value;

    const program: Program = {
        id: programId || generateProgramId(),
        name: formData.get('name') as string,
        institution: formData.get('institution') as string,
        advisor: (formData.get('advisor') as string) || undefined,
        status: formData.get('status') as Program['status'],
        applicationDeadline: (formData.get('applicationDeadline') as string) || undefined,
        interviewDate: (formData.get('interviewDate') as string) || undefined,
        decisionDate: (formData.get('decisionDate') as string) || undefined,
        notes: (formData.get('notes') as string) || undefined,
    };

    const programs = loadPrograms();

    if (programId) {
        // Update existing program
        const index = programs.findIndex(p => p.id === programId);
        if (index >= 0) {
            programs[index] = program;
        }
    } else {
        // Add new program
        programs.push(program);
    }

    savePrograms(programs);
    closeProgramModal(container);

    // Refresh the programs list
    const statusFilter = getCurrentStatusFilter();
    const programsContainer = container.querySelector('#programs-container');
    if (programsContainer) {
        programsContainer.innerHTML = renderProgramsList(programs, statusFilter);
        attachEditDeleteListeners(container);
    }
}

/**
 * Delete a program
 */
function deleteProgram(container: HTMLElement, programId: string): void {
    const programs = loadPrograms().filter(p => p.id !== programId);
    savePrograms(programs);

    // Refresh the programs list
    const statusFilter = getCurrentStatusFilter();
    const programsContainer = container.querySelector('#programs-container');
    if (programsContainer) {
        programsContainer.innerHTML = renderProgramsList(programs, statusFilter);
        attachEditDeleteListeners(container);
    }
}

/**
 * Get current status filter
 */
function getCurrentStatusFilter(): string {
    try {
        const stored = localStorage.getItem('program-tracker-status-filter');
        return stored || 'all';
    } catch (e) {
        return 'all';
    }
}

/**
 * Set status filter
 */
function setStatusFilter(filter: string): void {
    try {
        localStorage.setItem('program-tracker-status-filter', filter);
    } catch (e) {
        console.warn('Failed to save status filter:', e);
    }
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Utility: Format date
 */
function formatDate(dateString: string): string {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) {
        return dateString;
    }
}
