from typing import Dict, List
from urllib.parse import quote

def display_field_ids() -> Dict[str, str]:
    """
    Display available field IDs in a formatted table
    Returns: Dictionary mapping IDs to field names
    """
    fields = {
        '11': 'Agricultural and Biological Sciences',
        '12': 'Arts and Humanities',
        '13': 'Biochemistry, Genetics and Molecular Biology',
        '14': 'Business, Management and Accounting',
        '15': 'Chemical Engineering',
        '16': 'Chemistry',
        '17': 'Computer Science',
        '18': 'Decision Sciences',
        '19': 'Earth and Planetary Sciences',
        '20': 'Economics, Econometrics and Finance',
        '26': 'Mathematics',
        '27': 'Medicine',
        '28': 'Neuroscience',
        '29': 'Nursing',
        '30': 'Pharmacology, Toxicology and Pharmaceutics',
        '31': 'Physics and Astronomy',
        '32': 'Psychology',
        '33': 'Social Sciences',
        '34': 'Veterinary',
        '35': 'Dentistry',
        '36': 'Health Professions'
    }
    
    return fields

def build_works_filter(
    search_term: str,
    from_year: int = 1980,
    country_code: str = 'US',
    topic_ids: List[str] = None
) -> str:
    """
    Build filter string for works endpoint with configurable parameters
    Args:
        search_term: Term to search in titles and abstracts
        from_year: Start year for publication date filter
        country_code: Country code for institution filter
        topic_ids: List of topic IDs to filter by
    Returns:
        Formatted filter string for OpenAlex API
    """
    filters = [
        f'title_and_abstract.search:{quote(search_term)}',
        f'publication_year:>{from_year}',
        f'institutions.country_code:{country_code}'
    ]
    
    if topic_ids:
        filters.append(f'topics.field.id:{"|".join(topic_ids)}')
    
    return ','.join(filters)