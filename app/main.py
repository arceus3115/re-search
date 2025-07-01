import requests
import json
from typing import List, Dict
from academic_network import AcademicNetwork
from urllib.parse import urlencode
from helpers import display_field_ids, build_works_filter

BASE_URL = 'https://api.openalex.org/'
HEADERS = {
    'User-Agent': f'ResearchNetwork (kennedy.b.ho@gmail.com)',
    'Accept': 'application/json'
}

def main():
    # Get search parameters from user
    search_term = input("Enter a search term: ")
    from_year = input("Enter start year (default 1980): ") or "1980"
    country_code = input("Enter country code (default US): ") or "US"
    
    # Display field IDs and get user selection
    fields = display_field_ids()
    topic_ids = []
    
    print("\nEnter topic IDs (or press Enter when done)")
    while True:
        topic_id = input("Enter topic ID (or press Enter to finish): ").strip()
        if not topic_id:
            break
        if topic_id in fields:
            topic_ids.append(topic_id)
            print(f"Added: {fields[topic_id]}")
        else:
            print(f"Invalid ID. Please enter a valid ID from the table.")
    
    # Build the filter string using helper function
    endpoint = "works"
    filter_string = build_works_filter(
        search_term=search_term,
        from_year=int(from_year),
        country_code=country_code,
        topic_ids=topic_ids
    )

    url = f'{BASE_URL}{endpoint}?filter={filter_string}&sort=fwci:desc'
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    works = data.get('results', [])
    if not works:
        print("No results found.")
        return
    
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
        print(f"FWCI: {work.get('fwci', 'No FWCI')}")
        print("-" * 80)
        
    if not works:
        print("No works found for the search term.")

if __name__ == "__main__":
    main()
