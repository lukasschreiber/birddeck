from typing import List, Any


def paginate_elements(
    elements: List[Any], max_elements_per_page: int
) -> List[List[Any]]:
    """
    Paginate a list of elements, accounting for navigation buttons.

    - First page:
        - Slot for "back to parent" button.
        - Slot for "next page" button if more pages exist.
    - Following pages:
        - Slot for "back to previous page" button.
        - Slot for "next page" button if more pages exist.
    """
    if max_elements_per_page < 2:
        raise ValueError(
            "max_elements_per_page must be at least 2 to fit navigation buttons"
        )

    pages = []
    elements = sort_elements(elements)
    remaining_elements = elements.copy()
    page_index = 0

    while remaining_elements:
        # Determine reserved slots for this page
        if page_index == 0:
            # First page always reserves 1 slot for "back to parent"
            reserved_slots = 1
        else:
            # Following pages reserve 1 slot for "back to previous page"
            reserved_slots = 1

        # Check if a next page will exist
        if len(remaining_elements) > max_elements_per_page - reserved_slots:
            reserved_slots += 1  # reserve 1 slot for "next page" button

        slots_for_elements = max_elements_per_page - reserved_slots
        page_elements = remaining_elements[:slots_for_elements]
        remaining_elements = remaining_elements[slots_for_elements:]
        pages.append(page_elements)
        page_index += 1

    return pages

def sort_elements(elements: List[Any]) -> List[Any]:
    """
    Sort elements so that:
      - Favorites come first.
      - 'uncertain' types come last.
      - Exotic birds and groups follow regular entries within each favorite tier.
      - Exotic entries are sorted by country code before title.
      - Titles are sorted alphabetically (case-insensitive, ignoring hyphens).
    """
    return sorted(
        elements,
        key=lambda x: (
            x.get("type") == "uncertain",          # uncertain always last
            not x.get("favorite", False),          # favorites first
            x.get("exotic", False) if x.get("type") == "bird" or x.get("type") == "group" else False,             # exotic birds last but before uncertain
            (x.get("country") or "").strip().upper()
            if x.get("type") in ("bird", "group") and x.get("exotic", False)
            else "",
            x.get("title", "").lower().replace("-", ""),  # alphabetical
        ),
    )
