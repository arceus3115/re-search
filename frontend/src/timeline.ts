/**
 * Application Timeline Component for Graduate School Application Process
 */

export interface TimelineStep {
    id: number;
    title: string;
    description: string;
    timeline: string;
    suggestedMonths?: string[];
    status: 'pending' | 'in-progress' | 'complete';
}

const timelineSteps: Omit<TimelineStep, 'status'>[] = [
    {
        id: 1,
        title: 'Decide on schools to apply',
        description: 'Research and select target programs that align with your goals and interests.',
        timeline: 'By August',
        suggestedMonths: ['August']
    },
    {
        id: 2,
        title: 'GRE',
        description: 'Prepare for and take the Graduate Record Exam. General GRE can be taken year-round, ideally by summer. Psychology GRE (if applicable) is offered in April, October, and November.',
        timeline: 'Ideally by summer, Psychology GRE in April',
        suggestedMonths: ['April', 'Summer', 'October', 'November']
    },
    {
        id: 3,
        title: 'Contact advisors for recommendations',
        description: 'Request letters of recommendation from advisors and distribute materials to recommenders.',
        timeline: 'By early October',
        suggestedMonths: ['September', 'October']
    },
    {
        id: 4,
        title: 'Draft writing statement of purpose',
        description: 'Write and refine your personal statements and statements of purpose for each program.',
        timeline: 'September - November',
        suggestedMonths: ['September', 'October', 'November']
    },
    {
        id: 5,
        title: 'Program tracker',
        description: 'Track your applications through the interview process to final decisions.',
        timeline: 'Ongoing',
        suggestedMonths: ['September', 'October', 'November', 'December', 'January', 'February', 'March', 'April']
    }
];

/**
 * Get manual status override from localStorage
 */
function getManualStatus(stepId: number): 'pending' | 'in-progress' | 'complete' | null {
    try {
        const stored = localStorage.getItem(`timeline-step-${stepId}-status`);
        if (stored && ['pending', 'in-progress', 'complete'].includes(stored)) {
            return stored as 'pending' | 'in-progress' | 'complete';
        }
    } catch (e) {
        console.warn('Failed to read from localStorage:', e);
    }
    return null;
}

/**
 * Save manual status override to localStorage
 */
function saveManualStatus(stepId: number, status: 'pending' | 'in-progress' | 'complete'): void {
    try {
        localStorage.setItem(`timeline-step-${stepId}-status`, status);
    } catch (e) {
        console.warn('Failed to save to localStorage:', e);
    }
}

/**
 * Calculate step status based on current date and application year
 * Default behavior: returns "pending" unless manual override exists
 */
export function calculateStepStatus(step: Omit<TimelineStep, 'status'>, applicationYear: number, currentDate: Date = new Date()): 'pending' | 'in-progress' | 'complete' {
    // Check for manual override first - only use manual override if it exists
    const manualStatus = getManualStatus(step.id);
    if (manualStatus !== null) {
        return manualStatus;
    }

    // Default to "pending" on launch - disable automatic date-based calculation
    return 'pending';

    // Date-based calculation code (commented out - disabled by default)
    /*
    const currentMonth = currentDate.getMonth(); // 0-11 (Jan = 0, Aug = 7)
    const currentYear = currentDate.getFullYear();

    // Application cycle starts in August of the year before application year
    // For example, for 2025 application: cycle starts August 2024
    const cycleStartMonth = 7; // August (0-indexed)
    const cycleStartYear = applicationYear - 1;

    // Calculate current month in cycle (0 = August, 1 = September, etc.)
    let currentMonthInCycle: number;
    if (currentYear === cycleStartYear) {
        // Same year as cycle start
        currentMonthInCycle = currentMonth - cycleStartMonth;
    } else if (currentYear === applicationYear) {
        // Application year (months 5-8: Jan-Apr)
        currentMonthInCycle = 5 + currentMonth; // Jan = 5, Feb = 6, etc.
    } else {
        // Before cycle start or after application year
        if (currentYear < cycleStartYear) {
            return 'pending'; // Haven't started yet
        } else {
            return 'complete'; // After application year
        }
    }

    // Map step to expected month range in cycle
    // Month 0 = August (cycle start), Month 1 = September, etc.
    const stepMonthRanges: { [key: number]: { start: number; end: number } } = {
        1: { start: 0, end: 0 }, // August (month 0)
        2: { start: -4, end: 3 }, // April (before cycle) to October (month 3) - spans multiple months
        3: { start: 1, end: 2 }, // September to October (month 1-2)
        4: { start: 1, end: 3 }, // September to November (month 1-3)
        5: { start: 1, end: 8 }, // September to April (ongoing, month 1-8)
    };

    const range = stepMonthRanges[step.id];
    if (!range) return 'pending';

    // Handle step 2 (GRE) which starts before cycle
    if (step.id === 2) {
        // Can start in April (before cycle) or during cycle
        if (currentMonthInCycle < 0 && currentYear === cycleStartYear) {
            // Before August but in cycle start year - check if in April
            if (currentMonth === 3) { // April
                return 'in-progress';
            }
            return 'pending';
        }
    }

    if (currentMonthInCycle < range.start) {
        return 'pending';
    } else if (currentMonthInCycle >= range.start && currentMonthInCycle <= range.end) {
        return 'in-progress';
    } else {
        return 'complete';
    }
    */
}

/**
 * Get all timeline steps with calculated status
 */
export function getTimelineSteps(applicationYear: number = new Date().getFullYear() + 1): TimelineStep[] {
    return timelineSteps.map(step => ({
        ...step,
        status: calculateStepStatus(step, applicationYear)
    }));
}

/**
 * Render the timeline component
 */
export function renderTimeline(container: HTMLElement, applicationYear: number = new Date().getFullYear() + 1): void {
    const steps = getTimelineSteps(applicationYear);

    container.innerHTML = `
        <div class="application-timeline">
            <div class="timeline-header">
                <h3>Overview of Suggested Steps for Applying to Graduate School in Clinical Psychology</h3>
                <div class="timeline-year-selector">
                    <label for="application-year">Application Year:</label>
                    <input type="number" id="application-year" value="${applicationYear}" min="2024" max="2030" style="width: 100px; padding: 0.25rem; margin-left: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
                </div>
            </div>
            <div class="timeline-legend" style="display: flex; gap: 1.5rem; justify-content: center; margin-bottom: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 6px;">
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #28a745; width: 20px; height: 20px; border-radius: 50%; display: inline-block; margin-right: 0.5rem;"></span>
                    <span>Complete</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #ffc107; width: 20px; height: 20px; border-radius: 50%; display: inline-block; margin-right: 0.5rem;"></span>
                    <span>In Progress</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #6c757d; width: 20px; height: 20px; border-radius: 50%; display: inline-block; margin-right: 0.5rem;"></span>
                    <span>Pending</span>
                </div>
            </div>
            <div class="timeline-steps">
                ${steps.map(step => renderTimelineStep(step)).join('')}
            </div>
        </div>
    `;

    // Add event listener for year selector
    const yearInput = container.querySelector('#application-year') as HTMLInputElement;
    if (yearInput) {
        yearInput.addEventListener('change', () => {
            const newYear = parseInt(yearInput.value);
            if (!isNaN(newYear)) {
                renderTimeline(container, newYear);
            }
        });
    }

    // Add click handlers for status indicators
    container.querySelectorAll('.clickable-status').forEach(statusEl => {
        statusEl.addEventListener('click', (e) => {
            e.stopPropagation();
            const stepId = parseInt((statusEl as HTMLElement).getAttribute('data-step-id') || '0');
            if (stepId > 0) {
                cycleStepStatus(stepId, container, applicationYear);
            }
        });
    });

    // Add click handler for program tracker
    const programTrackerTitle = container.querySelector('[data-action="open-program-tracker"]');
    if (programTrackerTitle) {
        programTrackerTitle.addEventListener('click', () => {
            // Dispatch event to open program tracker
            window.dispatchEvent(new CustomEvent('open-program-tracker'));
        });
    }
}

function cycleStepStatus(stepId: number, container: HTMLElement, applicationYear: number): void {
    const steps = getTimelineSteps(applicationYear);
    const step = steps.find(s => s.id === stepId);
    if (!step) return;

    // Cycle: pending -> in-progress -> complete -> pending
    const statusCycle: ('pending' | 'in-progress' | 'complete')[] = ['pending', 'in-progress', 'complete'];
    const currentIndex = statusCycle.indexOf(step.status);
    const nextIndex = (currentIndex + 1) % statusCycle.length;
    const newStatus = statusCycle[nextIndex];

    // Save manual override
    saveManualStatus(stepId, newStatus);

    // Re-render timeline
    renderTimeline(container, applicationYear);
}

function renderTimelineStep(step: TimelineStep): string {
    const statusColors = {
        'complete': '#28a745',
        'in-progress': '#ffc107',
        'pending': '#6c757d'
    };

    const statusIcons = {
        'complete': '✓',
        'in-progress': '⟳',
        'pending': '○'
    };

    const color = statusColors[step.status];
    const icon = statusIcons[step.status];

    // Special handling for step 2 (GRE) - make it clickable
    const isGRE = step.id === 2;
    const isProgramTracker = step.id === 5;

    // Special handling for step 5 (Program Tracker) - make it clickable
    const titleElement = isGRE
        ? `<h4 class="timeline-step-title" style="cursor: pointer; text-decoration: underline; color: #007bff;" onclick="window.open('https://www.ets.org/gre', '_blank')">${step.title} →</h4>`
        : isProgramTracker
        ? `<h4 class="timeline-step-title" style="cursor: pointer; text-decoration: underline; color: #007bff;" data-action="open-program-tracker">${step.title} →</h4>`
        : `<h4 class="timeline-step-title">${step.title}</h4>`;

    return `
        <div class="timeline-step" data-step-id="${step.id}" data-status="${step.status}">
            <div class="timeline-step-connector"></div>
            <div class="timeline-step-content">
                <div class="timeline-step-header">
                    <div class="timeline-step-number" style="background-color: ${color};">
                        ${step.id}
                    </div>
                    <div class="timeline-step-status clickable-status" style="color: ${color}; cursor: pointer;" data-step-id="${step.id}" title="Click to change status">
                        <span class="status-icon">${icon}</span>
                        <span class="status-text">${step.status === 'in-progress' ? 'In Progress' : step.status === 'complete' ? 'Complete' : 'Pending'}</span>
                    </div>
                </div>
                <div class="timeline-step-body">
                    ${titleElement}
                    <p class="timeline-step-description">${step.description}</p>
                    <div class="timeline-step-meta">
                        <span class="timeline-label">Timeline:</span>
                        <span class="timeline-value">${step.timeline}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}
