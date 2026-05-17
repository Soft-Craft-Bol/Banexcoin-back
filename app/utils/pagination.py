
from math import ceil
from typing import Any


def paginate_list(items: list[Any], page: int = 0, size: int = 20):
    if page < 0:
        page = 0

    if size <= 0:
        size = 20

    if size > 200:
        size = 200

    total_elements = len(items)
    total_pages = ceil(total_elements / size) if total_elements > 0 else 0

    start = page * size
    end = start + size

    content = items[start:end]

    return {
        "content": content,
        "pageable": {
            "page_number": page,
            "page_size": size,
            "offset": start,
            "paged": True,
            "unpaged": False,
        },
        "total_elements": total_elements,
        "total_pages": total_pages,
        "last": page >= total_pages - 1 if total_pages > 0 else True,
        "first": page == 0,
        "size": size,
        "number": page,
        "number_of_elements": len(content),
        "empty": len(content) == 0,
    }