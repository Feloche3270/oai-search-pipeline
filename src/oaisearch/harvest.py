import time
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

from oaisearch.errors import OAIError

NAMESPACE = {"oai": "http://www.openarchives.org/OAI/2.0/"}


def fetch_data(client: httpx.Client, endpoint: str, params: dict[str, str]) -> bytes:
    response = client.get(endpoint, params=params)
    # OAI erros normally come back with HTTP 200 as the OAI-PMH spec requires
    # but Zenodo doesn't follow it and sends OAI error with 422 status.
    if response.status_code == 422:
        return response.content
    response.raise_for_status()
    return response.content


def save_data(content: bytes, out_dir: Path, page_number: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    page_path = out_dir / f"page_{page_number:04d}.xml"
    page_path.write_bytes(content)
    return page_path


def parse_resumption_token(content: bytes) -> str | None:
    root = ET.fromstring(content)
    resumption_token = root.find(".//oai:resumptionToken", NAMESPACE)
    if resumption_token is None:
        return None
    token = resumption_token.text
    if token is None or token.strip() == "":
        return None
    return token.strip()


def count_records(content: bytes) -> int:
    root = ET.fromstring(content)
    records = root.findall(".//oai:record", NAMESPACE)
    count_record = len(records)
    return count_record


def check_oai_error(content: bytes) -> None:
    root = ET.fromstring(content)
    oai_error = root.find(".//oai:error", NAMESPACE)
    if oai_error is None:
        return
    error_code = oai_error.get("code", "unknown")
    error_message = oai_error.text
    if error_message is None:
        error_message = ""
    raise OAIError(error_code, error_message.strip())


def harvest(
    client: httpx.Client,
    endpoint: str,
    metadata_prefix: str,
    set_spec: str,
    out_dir: Path,
    max_records: int,
    delay: float = 1.0,
) -> int:
    verb = "ListRecords"
    page_number = 0
    total_records = 0
    params = {"verb": verb, "metadataPrefix": metadata_prefix, "set": set_spec}
    while True:
        content = fetch_data(client, endpoint, params)
        try:
            check_oai_error(content)
        except OAIError as err:
            if err.code == "noRecordsMatch":
                return total_records
            raise
        page_number += 1
        file = save_data(content, out_dir, page_number)
        print(file)
        total_records += count_records(content)
        resumption_token = parse_resumption_token(content)
        if resumption_token is None or total_records >= max_records:
            break
        params = {"verb": verb, "resumptionToken": resumption_token}
        time.sleep(delay)
    return total_records


if __name__ == "__main__":
    metadata_prefix = "oai_dc"
    set_spec = "user-waterlat-gobacit"
    out_dir = Path("data") / metadata_prefix / set_spec
    headers = {
        "user-agent": "oai-search/0.1 (+https://github.com/Feloche3270/oai-search-pipeline)"
    }
    endpoint = "https://zenodo.org/oai2d"

    with httpx.Client(headers=headers, timeout=60.0) as client:
        harvest(client, endpoint, metadata_prefix, set_spec, out_dir, 500)
