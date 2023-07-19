from typing import TypedDict, Optional

class CollectionObj(TypedDict):
    id: str
    title: str
    start_date: str
    end_date: str
    bbox: str
    metadata: Optional[str]
    href: Optional[str]
    description: str
    license: str