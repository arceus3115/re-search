import requests
import json
from typing import Dict, List, Optional
from urllib.parse import quote, urlencode

BASE_URL = 'https://api.openalex.org/'
HEADERS = {
    'User-Agent': f'ResearchNetwork (kennedy.b.ho@vanderbilt.edu)',
    'Accept': 'application/json'
}

class AcademicNetwork:
    def __init__(self):
        self.institutions = []
        self.authors = []
        self.works = []
        self.topics = []

    def add_institution(self, name: str) -> Optional[Dict]:
        """Search and add institution to network with improved display and selection"""
        try:
            endpoint = 'institutions'
            url = f'{BASE_URL}{endpoint}?filter=display_name.search:{quote(name)}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if not data.get('results'):
                print(f"No institutions found matching '{name}'")
                return None

            # Display all matches for selection
            print("\nMatching institutions:")
            for i, inst in enumerate(data['results'], 1):
                print(
                    f"{i}. {inst['display_name']} "
                    f"({inst.get('country_code', 'N/A')}) - "
                    f"Works: {inst.get('works_count', 0):,}"
                    f""
                )

            # Let user select the correct institution
            while True:
                try:
                    selection = input("\nSelect institution number (or 0 to skip): ")
                    if not selection.strip():
                        return None
                        
                    idx = int(selection)
                    if idx == 0:
                        return None
                    if 1 <= idx <= len(data['results']):
                        institution = data['results'][idx - 1]
                        self.institutions.append(institution)
                        print(f"\nAdded: {institution['display_name']}")
                        return institution
                    print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

        except requests.RequestException as e:
            print(f"Error searching for institution: {e}")
            return None

    def add_affiliated_authors(self, institution_id: str) -> List[Dict]:
        """Find authors affiliated with an institution"""
        response = requests.get(
            f"{BASE_URL}authors",
            params={
                'filter': f'last_known_institutions.id:{institution_id}',
                'sort': 'summary_stats.h_index:desc',
                'per-page': 100
            },
            headers=HEADERS
        )
        data = response.json()
        if data.get('results'):
            self.authors.extend(data['results'])
            return data['results']
        return []
    def add_author(self, author_name: str) -> Optional[Dict]:
        """Search and add author to network"""
        try:
            endpoint = 'authors'
            url = f'{BASE_URL}{endpoint}?filter=display_name.search:{quote(author_name)}'
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if not data.get('results'):
                print(f"No authors found matching '{author_name}'")
                return None

            # Display all matches for selection
            print("\nMatching authors:")
            for i, author in enumerate(data['results'], 1):
                print(
                    f"{i}. {author['display_name']} "
                    f"({author.get('last_known_institution', {}).get('display_name', 'N/A')}) - "
                    f"H-Index: {author['summary_stats']['h_index']}, "
                    f"Works: {author.get('works_count', 0):,}"
                )

            # Let user select the correct author
            while True:
                try:
                    selection = input("\nSelect author number (or 0 to skip): ")
                    if not selection.strip():
                        return None
                        
                    idx = int(selection)
                    if idx == 0:
                        return None
                    if 1 <= idx <= len(data['results']):
                        author = data['results'][idx - 1]
                        self.authors.append(author)
                        print(f"\nAdded: {author['display_name']}")
                        return author
                    print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

        except requests.RequestException as e:
            print(f"Error searching for author: {e}")
            return None

    def add_author_works(self, author_id: str) -> List[Dict]:
        """Get works by an author"""
        response = requests.get(
            f"{BASE_URL}works",
            params={
                'filter': f'author.id:{author_id}',
                'sort': 'cited_by_count:desc',
                'per-page': 25
            },
            headers=HEADERS
        )
        data = response.json()
        if data.get('results'):
            self.works.extend(data['results'])
            return data['results']
        return []

    def get_affiliations_from_works(self, works: List[Dict]) -> List[str]:
        """Extracts unique institution names from a list of works."""
        affiliations = set()
        for work in works:
            for author in work.get('authorships', []):
                institution = author.get('institutions')
                if institution:
                    for inst in institution:
                        display_name = inst.get('display_name')
                        if display_name:
                            affiliations.add(display_name)
        return list(affiliations)
