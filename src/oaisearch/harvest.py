import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

OAI_NAMESPACE = {"oai": "http://www.openarchives.org/OAI/2.0/"}


def fetch_data(client: httpx.Client, endpoint: str, params: dict[str, str]) -> bytes:
    response_dc = client.get(endpoint, params=params)
    response_dc.raise_for_status()
    return response_dc.content


def save_data(content: bytes, out_dir: Path, page_number: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    page_path = out_dir / f"page_{page_number:04d}.xml"
    page_path.write_bytes(content)
    return page_path


def parse_resumption_token(content: bytes) -> str | None:
    root = ET.fromstring(content)
    resumption_token = root.find(".//oai:resumptionToken", OAI_NAMESPACE)
    if resumption_token is None:
        return None
    elif resumption_token.text is None or resumption_token.text.strip() == "":
        return None
    return resumption_token.text.strip()


if __name__ == "__main__":
    verb = "ListRecords"
    metadata_prefix = "oai_dc"
    set_spec = "user-waterlat-gobacit"
    out_dir = Path("data") / metadata_prefix / set_spec
    headers = {
        "user-agent": "oai-search/0.1 (+https://github.com/Feloche3270/oai-search-pipeline)"
    }
    params = {"verb": verb, "metadataPrefix": metadata_prefix, "set": set_spec}
    endpoint = "https://zenodo.org/oai2d"
    page_number = 1

    with httpx.Client(headers=headers, timeout=60.0) as client:
        content = fetch_data(client, endpoint, params)
        path = save_data(content, out_dir, page_number)
    print(path)
    resumption_token = parse_resumption_token(content)
    print(resumption_token)
