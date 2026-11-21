import html
import re
import xml.etree.ElementTree as ET

from pathlib import Path

from oaisearch.models import Record
from oaisearch.namespaces import NAMESPACES

PATTERN_DOI = re.compile(r"10\.\d{4,9}\/\S+")
PATTERN_TAG = re.compile(r"<[^>]+>")


def get_texts(metadata: ET.Element, tag: str) -> list[str]:
    elements = metadata.findall(f"dc:{tag}", NAMESPACES)
    stripped_texts = [(element.text or "").strip() for element in elements]
    texts = [text for text in stripped_texts if text]
    return texts


def extract_year(dates: list[str]) -> int | None:
    for date in dates:
        year = date[:4]
        if year.isdigit():
            return int(year)
    return None


def extract_doi(identifiers: list[str]) -> str | None:
    for identifier in identifiers:
        match = PATTERN_DOI.search(identifier)
        if match:
            doi = match.group()
            return doi
    return None


def clean_description(description: list[str]) -> str | None:
    if not description:
        return None
    html_description = html.unescape(description[0])
    no_html_description = PATTERN_TAG.sub(" ", html_description)
    clean_description = " ".join(no_html_description.split())
    if clean_description == "":
        return None
    return clean_description


def parse_record(record: ET.Element, source: str) -> Record | None:
    element_identifier = record.find("oai:header/oai:identifier", NAMESPACES)
    if element_identifier is None:
        return None
    if element_identifier.text is None:
        return None
    identifier = element_identifier.text.strip()
    metadata = record.find("oai:metadata/oai_dc:dc", NAMESPACES)
    if metadata is None:
        return None
    titles = get_texts(metadata, "title")
    identifiers = get_texts(metadata, "identifier")
    dates = get_texts(metadata, "date")
    descriptions = get_texts(metadata, "description")
    languages = get_texts(metadata, "language")
    title = titles[0] if titles else ""
    creators = get_texts(metadata, "creator")
    subjects = get_texts(metadata, "subject")
    publication_year = extract_year(dates)
    description = clean_description(descriptions)
    doi = extract_doi(identifiers)
    language = languages[0] if languages else None

    return Record(
        identifier=identifier,
        title=title,
        source=source,
        creators=creators,
        subjects=subjects,
        publication_year=publication_year,
        description=description,
        doi=doi,
        language=language,
    )


def parse_page(content: bytes, source: str) -> list[Record]:
    records: list[Record] = []
    root = ET.fromstring(content)
    record_element = root.findall(".//oai:record", NAMESPACES)
    for record in record_element:
        parsed = parse_record(record, source)
        if parsed is not None:
            records.append(parsed)
    return records


def load_records(folder: Path, source: str) -> list[Record]:
    records: list[Record] = []
    for page in sorted(folder.glob("page_*.xml")):
        content = page.read_bytes()
        records_page = parse_page(content, source)
        records.extend(records_page)
    return records