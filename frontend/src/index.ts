
import { renderLandingPage, showAuthorWorksModal } from './ui';
import { fetchAuthorWorks, fetchAuthorDetails } from './api';

document.addEventListener('DOMContentLoaded', () => {
    const appDiv = document.getElementById('root');
    if (!appDiv) {
        console.error('Root element not found!');
        return;
    }

    // Initial render: landing page
    renderLandingPage(appDiv);

    // Event listener for author links
    document.addEventListener('click', async (event) => {
        const target = event.target as HTMLElement;
        if (target.classList.contains('author-link')) {
            event.preventDefault();
            const authorId = target.dataset.authorId?.split('/').pop();
            const authorName = target.dataset.authorName;

            if (authorId && authorName) {
                try {
                    const authorDetailsData = await fetchAuthorDetails(authorId);
                    console.log('Author details data:', authorDetailsData);
                    const authorInstitution = authorDetailsData.author?.last_known_institutions?.map((inst: any) => inst.display_name).join(', ') || 'N/A';
                    console.log('Author institution:', authorInstitution);

                    const worksData = await fetchAuthorWorks(authorId);
                    const works = worksData.works;

                    let worksHtml = '';
                    if (works && works.length > 0) {
                        worksHtml = '<ul>';
                        works.forEach((work: any) => {
                            worksHtml += `
                                <li>
                                    <h5>${work.title || 'No Title'}</h5>
                                    <p><strong>Authors:</strong> ${work.authorships.map((a: any) => a.author.display_name).join(', ') || 'N/A'}</p>
                                    <p><strong>Affiliations:</strong> ${work.authorships.flatMap((a: any) => a.institutions.map((i: any) => i.display_name)).filter((name: string) => name).join(', ') || 'N/A'}</p>
                                    <p><strong>FWCI:</strong> ${work.fwci || 'N/A'}</p>
                                </li>
                            `;
                        });
                        worksHtml += '</ul>';
                    } else {
                        worksHtml = '<p>No other works found for this author.</p>';
                    }

                    showAuthorWorksModal(authorName, authorInstitution, worksHtml);

                } catch (error) {
                    console.error('Error fetching author works or details:', error);
                    alert('Failed to fetch author works or details. Please try again.');
                }
            }
        }
    });
});
