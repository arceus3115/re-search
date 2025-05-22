import requests
import json
from typing import List, Dict
from academic_network import AcademicNetwork
from urllib.parse import quote, urlencode

BASE_URL = 'https://api.openalex.org/'
HEADERS = {
    'User-Agent': f'ResearchNetwork (kennedy.b.ho@vanderbilt.edu)',
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
    network = AcademicNetwork()
    
    # Step 1: Add Institutions
    while True:
        institution_name = input("\nEnter institution name (or 'done' to continue): ")
        if institution_name.lower() == 'done':
            break
        
        institution = network.add_institution(institution_name)
        if institution:
            # Step 2: Get affiliated authors
            print("\nFinding top affiliated authors...")
            authors = network.add_affiliated_authors(institution['id'])
            print(f"Found {len(authors)} authors")
            
            # Display top authors for selection
            for i, author in enumerate(authors, 1):
                print(f"{i}. {author['display_name']} - H-Index: {author['summary_stats']['h_index']}, ")
            
            # Step 3: Select specific authors to include
            author_indices = input("\nEnter author numbers to include (comma-separated): ")
            selected_indices = [int(i.strip()) - 1 for i in author_indices.split(',')]
            
            # Get works for selected authors
            for idx in selected_indices:
                if 0 <= idx < len(authors):
                    author = authors[idx]
                    print(f"\nGetting works for {author['display_name']}...")
                    works = network.add_author_works(author['id'])
                    print(f"Added {len(works)} works")

    # Step 2: Add Authors (Independent of institutions, or if no institution is provided)
    while True:
        author_name = input("\nEnter author name (or 'done' to continue): ")
        if author_name.lower() == 'done':
            break
        author = network.add_author(author_name)
        if author:
            print(f"Added author: {author['display_name']}")
            works = network.add_author_works(author['id'])
            print(f"Added {len(works)} works")
        else:
            print("Author not found or already added.")

    # Step 3: Search for topics
    while True:
        # Get topics from user
        topics_input = input("\nEnter topics of focus (comma-separated): ")
        topics = [topic.strip() for topic in topics_input.split(',') if topic.strip()]
        if topics_input.lower() == 'done':
            break
        print("\nSearching for topics...")
        results = search_topics(topics)
        
        if results:
            print("\nMatching topics:")
            for i, topic in enumerate(results, 1):
                print(
                    f"{i}. {topic['display_name']} - "
                    f"Works: {topic.get('works_count', 0):,}, "
                    f"Level: {topic.get('level', 'N/A')}"
                )
        else:
            print("No topics found matching your search.")
    

    # Display network summary
    print("\nNetwork Summary:")
    print(f"Institutions: {len(network.institutions)}")
    print(f"Authors: {len(network.authors)}")
    print(f"Works: {len(network.works)}")
    
    # Save network data
    with open('academic_network.json', 'w') as f:
        json.dump({
            'institutions': network.institutions,
            'authors': network.authors,
            'works': network.works
        }, f, indent=2)
    print("\nNetwork data saved to academic_network.json")

if __name__ == "__main__":
    main()