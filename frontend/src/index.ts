
import { renderLandingPage } from './ui';

document.addEventListener('DOMContentLoaded', () => {
    const appDiv = document.getElementById('root');
    if (!appDiv) {
        console.error('Root element not found!');
        return;
    }

    // Initial render: landing page
    renderLandingPage(appDiv);
});
