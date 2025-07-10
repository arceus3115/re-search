from typing import Dict, List, Optional


class AcademicNetwork:
    def __init__(self):
        self.institutions = []
        self.authors = []
        self.works = []
        self.topics = []

    def get_affiliations_from_works(self, works: List[Dict]) -> List[str]:
        """Extracts unique institution names from a list of works."""
        affiliations = set()
        for work in works:
            for author in work.get("authorships", []):
                institution = author.get("institutions")
                if institution:
                    for inst in institution:
                        display_name = inst.get("display_name")
                        if display_name:
                            affiliations.add(display_name)
        return list(affiliations)
