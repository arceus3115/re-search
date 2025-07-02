from typing import Dict, List
from urllib.parse import quote

def display_field_ids() -> Dict[str, str]:
    """Returns a hardcoded dictionary of academic field IDs and their corresponding names.

    This function provides a static mapping of field IDs to human-readable names,
    which can be used for filtering or displaying options in a user interface.

    Returns:
        Dict[str, str]: A dictionary where keys are string representations of field IDs
                        and values are the full names of the academic fields.
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
    """Constructs a filter string for the OpenAlex API's /works endpoint.

    This function takes various search parameters and formats them into a query
    string suitable for filtering academic works in the OpenAlex API.

    Args:
        search_term (str): The primary term to search within the titles and abstracts of works.
        from_year (int, optional): The minimum publication year for the works. Defaults to 1980.
        country_code (str, optional): The two-letter country code (ISO 3166-1 alpha-2)
                                      to filter works by the institution's country. Defaults to 'US'.
        topic_ids (List[str], optional): A list of topic IDs to filter works by specific academic fields.
                                         If provided, works will match any of the given topic IDs.
                                         Defaults to None.

    Returns:
        str: A comma-separated string of filters, URL-encoded where necessary,
             ready to be appended to the OpenAlex API /works endpoint URL.
    """
    filters = [
        f'title_and_abstract.search:{quote(search_term)}',
        f'publication_year:>{from_year}',
        f'institutions.country_code:{country_code}'
    ]
    
    if topic_ids:
        filters.append(f'topics.field.id:{"|".join(topic_ids)}')
    
    return ','.join(filters)