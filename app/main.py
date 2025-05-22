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

def search_topics(topics: List[str]) -> List[Dict]:
    """Search for topics using OR filter"""    

    #topics seperated by 'OR'
    filters = 'AND'.join([quote(topic) for topic in topics])


    url = f"{BASE_URL}topics?search={filters}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    data = response.json()
    return data.get('results', [])

def main():
    quote = input("Enter a search term: ")
    endpoint = "works"
    url = f'{BASE_URL}{endpoint}?filter=title_and_abstract.search:{quote},publication_year:>1980'

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
Works: by the key words (search)
- filter: > 50 years old : filter=publication_year:>1980
- display: title, topics, concepts, keywords, authorships.institutions.ror (alias: institutions.ror) — Institutions affiliated with the authors of a work (ROR ID), FWCI
'''


if __name__ == "__main__":
    main()
