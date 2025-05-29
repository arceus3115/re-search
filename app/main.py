import requests
import json
from typing import List, Dict
from academic_network import AcademicNetwork
from urllib.parse import quote, urlencode

BASE_URL = 'https://api.openalex.org/'
HEADERS = {
    'User-Agent': f'ResearchNetwork (kennedy.b.ho@gmail.com)',
    'Accept': 'application/json'
}

def build_works_filter(
    search_term: str,
    from_year: int = 1980,
    country_code: str = 'US',
    topic_ids: List[str] = None
) -> str:
    """Build filter string for works endpoint with configurable parameters"""
    filters = [
        f'title_and_abstract.search:{quote(search_term)}',
        f'publication_year:>{from_year}',
        f'institutions.country_code:{country_code}'
    ]
    
    if topic_ids:
        filters.append(f'topics.field.id:{"|".join(topic_ids)}')
    
    return ','.join(filters)

def main():
    # Get search parameters from user
    search_term = input("Enter a search term: ")
    from_year = input("Enter start year (default 1980): ") or "1980"
    country_code = input("Enter country code (default US): ") or "US"
    
    # Get topic IDs
    print("\nEnter topic IDs (or press Enter when done)")
    print("Example IDs: 36 (Health), 27 (Medicine), 28 (Neuroscience), 32 (Psychology)")
    topic_ids = []
    while True:
        topic_id = input("Enter topic ID (or press Enter to finish): ").strip()
        if not topic_id:
            break
        topic_ids.append(topic_id)

    # Build the filter string
    endpoint = "works"
    filter_string = build_works_filter(
        search_term=search_term,
        from_year=int(from_year),
        country_code=country_code,
        topic_ids=topic_ids
    )

    print(f"{filter_string}")


    url = f'{BASE_URL}{endpoint}?filter={filter_string}'
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    works = data.get('results', [])
    if not works:
        print("No results found.")
        return
    
    print(f"Found {len(works)} works for the search term '{quote}'")
    for work in works:
        title = work.get('title', 'No title')
        authorships = work.get('authorships', [])

        
        affiliations = [authorship.get('institutions', []) for authorship in authorships]
        authors = [authorship.get('author', {}).get('display_name', 'No author name') for authorship in authorships]

        # display the affiliations
        affiliations = []
        for authorship in authorships:
            institutions = authorship.get('institutions', [])
            for institution in institutions:
                affiliation = institution.get('display_name', 'No affiliation')
                affiliations.append(affiliation)
        # Remove duplicates
        affiliations = list(set(affiliations))
        # Remove empty affiliations
        affiliations = [affiliation for affiliation in affiliations if affiliation]

        # display the authors
        authors = []
        for authorship in authorships:
            author = authorship.get('author', {})
            author_name = author.get('display_name', 'No author name')
            authors.append(author_name)
        # Remove duplicates
        authors = list(set(authors))
        # Remove empty authors
        authors = [author for author in authors if author]


        # Join the affiliations into a single string
        affiliation_text = ', '.join(affiliations)
        # Print the work details
        print(f"Title: {title}")
        print(f"Affiliations: {affiliation_text}")
        print(f"Authors: {', '.join(authors)}")
        print("-" * 80)
    # Move this outside the loop

    if not works:
        print("No works found for the search term.")
    '''
    Get a list of information about the works (Filter all for US based)
        - titles of the works 
        - authors of the works
        - insituations of the works
            - institutions.ror


'''

'''
Works: by the key words (search)
- filter: > 50 years old : filter=publication_year:>1980
- display: title, topics, concepts, keywords, authorships.institutions.ror (alias: institutions.ror) — Institutions affiliated with the authors of a work (ROR ID), FWCI
'''


if __name__ == "__main__":
    main()
