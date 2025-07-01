# re-search

## Notes
Discover researchers closest to you
Data Sources: OpenAlex, ORCID, PubMed (all have apis)
Structure: Name, ORCID, AlexID

- Start with inputting yourself, apply your direct links which would be 
"Personal" links, and your intended areas of focus. 
- For Researcher / PHD Search
	- Find closest links between you & your 1st degrees to the
	researcher in question
    - For Conference
    - Find researcher by topic
    - Find researcher by institution
    - Find link to a specific researcher
    - For Researcher / PHD Search
    - Find closest links between you & your 1st degrees to the
    researcher in question
- For Conference
	- Find researcher by topic 
	- Find researcher by institution
	- Find link to a specific researcher

## Steps
- [ ] User: ask for each group: seperate by ',' : institutions, authors, works, focus topic
    - [ ] Topic Options: search
- [ ] Making the user links
    - [ ] hiearchy of connections: 1,2, .., n : authors, institutions, works, 
    - [ ] works data gatherer: based on your works, make the hiearchy of connections

## Plan
- PHD PI Finder: cities, topics (trauma or memory or trauma and memory), selective pick departments () -> affiliate colleges + topics of focus -> ranked by prominence (h-index or etc)
	- topics: domain > field > subfield 
	- ask for the topics, separate by + sign, e
		- eg: memory & trauma, clinical psychology, psychology, nueroscience
	-> search topics: within the last 50 years, go 
- Conference: input people (build network) (one degree apart) -> input a conference -> search that conference for people one degree apart

- Search for WORKS (look for topics that include all your topics [can choose inclusive or exclusive]) -> search topics

## Development Roadmap

### Next Steps
1. Data Collection
   - [ ] Get list of available topic IDs from OpenAlex
    - https://docs.google.com/spreadsheets/d/1v-MAq64x4YjhO7RWcB-yrKV5D_2vOOsxl4u6GBKEXY8/edit?usp=sharing
    - https://docs.google.com/document/d/1bDopkhuGieQ4F8gGNj7sEc8WSE8mvLZS/edit?tab=t.0
   - [ ] Get list of available country codes
   - [ ] Implement work filtering by:
     - Citation count
     - Citation momentum
     - Search term relevance
   - [ ] Gather author and affiliation data
   - [ ] Rank results by h-index
   - [ ] Implement web crawler for PhD program verification

2. Work Information Collection (US Focus)
   - [ ] Titles
   - [ ] Authors
   - [ ] Institutions (using ROR IDs)

### API Query Parameters

#### Works Filtering
- Publication Date: `filter=publication_year:>1980`
- Location: `filter=institutions.country_code:US`

#### Display Fields
- Title
- Topics
- Concepts
- Keywords
- Institution affiliations
  - Using `authorships.institutions.ror` or `institutions.ror`
- Field-Weighted Citation Impact (FWCI)

### Data Structure
```json
{
    "work": {
        "title": "string",
        "publication_year": "integer",
        "authorships": [{
            "author": {},
            "institutions": [{
                "ror": "string",
                "name": "string"
            }]
        }],
        "topics": [],
        "concepts": [],
        "metrics": {
            "citations": "integer",
            "fwci": "float"
        }
    }
}
```
## Step 1 
- Get the top works 
- Get the top universities 

## Step 2
- Go through each university webpage provided by the open alex api 
    - check if there is a department name attatched to the string in the work for where they worked and see if you can route to the website 