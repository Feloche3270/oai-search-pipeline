from dataclasses import dataclass, field


@dataclass
class Record:
    """Common metadata model, independent of the source
    format (Dublin Core, DataCite)"""

    identifier: str
    title: str
    source: str
    creators: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    publication_year: int | None = None
    description: str | None = None
    doi: str | None = None
    language: str | None = None
