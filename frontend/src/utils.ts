export function cleanUniversityName(name: string): string {
    return name.replace(/\s*\([^)]*\)/g, '').trim();
}

export function renderCards<T>(containerElement: HTMLElement, data: T[], cardHtmlGenerator: (item: T) => string, cardClasses: string[], gridClass: string) {
    containerElement.innerHTML = ''; // Clear previous results

    if (data && data.length > 0) {
        const gridContainer = document.createElement('div');
        gridContainer.classList.add(gridClass);

        data.forEach(item => {
            const card = document.createElement('div');
            card.classList.add(...cardClasses);
            card.innerHTML = cardHtmlGenerator(item);
            gridContainer.appendChild(card);
        });
        containerElement.appendChild(gridContainer);
    } else {
        containerElement.innerHTML = '<p>No results found.</p>';
    }
}