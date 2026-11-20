import time
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

from oaisearch.errors import HarvestError, OAIError

NAMESPACE = {"oai": "http://www.openarchives.org/OAI/2.0/"}
RETRY_STATUSES = {429, 500, 502, 503, 504}
DEFAULT_HEADER = {
    "user-agent": "oai-search/0.1 (+https://github.com/Feloche3270/oai-search-pipeline)"
}


def fetch_data(client: httpx.Client, endpoint: str, params: dict[str, str]) -> bytes:
    response = client.get(endpoint, params=params)
    # OAI errors normally come back with HTTP 200 as the OAI-PMH spec requires
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


def parse_retry_after(retry_after: str | None) -> float | None:
    if retry_after is None:
        return None
    try:
        return float(retry_after)
    except ValueError:
        return None


def fetch_with_retry(
    client: httpx.Client,
    endpoint: str,
    params: dict[str, str],
    max_attempts: int = 3,
    backoff: float = 1.0,
) -> bytes:
    for attempt in range(max_attempts):
        wait = backoff * 2**attempt
        try:
            return fetch_data(client, endpoint, params)
        except httpx.HTTPStatusError as err:
            if err.response.status_code not in RETRY_STATUSES:
                raise
            if attempt == max_attempts - 1:
                raise
            if err.response.status_code == 429:
                retry_after = err.response.headers.get("Retry-After")
                retry_after_seconds = parse_retry_after(retry_after)
                if retry_after_seconds is not None:
                    wait = retry_after_seconds
            reason = f"HTTP {err.response.status_code}"
        except httpx.TransportError as err:
            if attempt == max_attempts - 1:
                raise
            reason = str(err)
        print(f"Retrying in {wait}s ({reason})")
        time.sleep(wait)
    raise RuntimeError("Unreachable")


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
        content = fetch_with_retry(client, endpoint, params)
        try:
            check_oai_error(content)
        except OAIError as err:
            if err.code == "noRecordsMatch":
                return total_records
            raise
        except ET.ParseError:
            raise HarvestError("Response is not valid XML.") from None
        page_number += 1
        save_data(content, out_dir, page_number)
        total_records += count_records(content)
        resumption_token = parse_resumption_token(content)
        if resumption_token is None or total_records >= max_records:
            break
        params = {"verb": verb, "resumptionToken": resumption_token}
        time.sleep(delay)
    return total_records
