from pathlib import Path

import httpx
import pytest

from oaisearch.errors import HarvestError, OAIError
from oaisearch.harvest import (
    check_oai_error,
    count_records,
    fetch_with_retry,
    harvest,
    parse_resumption_token,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_resumption_token_with_token():
    path_file = FIXTURES / "page_with_token.xml"
    data = path_file.read_bytes()
    result = parse_resumption_token(data)
    assert (
        result
        == ".eJyNjdFugjAARf-lz7jQIrqR-KAb7UIENxhU-mJKW5FRxACuZMZ_H9kHLLs5jyfn3kCvlASe_"
        "fBoL6C7nC-gs5xAjgUuvFTAQxaoDe_KHni3SR6AB6696maGD6rTfJiVbcFFNQALNGrgkg_"
        "8rVPHapzEllcHKcDdAr3oWq0P1XQFMNHXHI2QkeyYo6erJNlc4icoqa5fzhiyfeBm5KSLmml"
        "JonY95iaEGgnqhhTjJIand-prJyFxs8M4Xk97jnGabAQVn7mJX1ND6zEVBIbczmyG4DHyL4Ecm"
        "ZN8xxvVnPIow8mWjrTYs8uOutviQ59_O_ksCso5VQ3uQ-IuRA1TddZfezs10jdo58OA_btj_"
        "90xqxW4_wBokH0j.awBlYw.MXHdEUN4cVJnxhQwVhWd_AKOzZQ"
    )


def test_parse_resumption_token_without_token():
    path_file = FIXTURES / "last_page.xml"
    data = path_file.read_bytes()
    result = parse_resumption_token(data)
    assert result is None


def test_parse_resumption_token_without_field():
    path_file = FIXTURES / "complete_and_missing_fields.xml"
    data = path_file.read_bytes()
    result = parse_resumption_token(data)
    assert result is None


def test_count_records():
    path_file = FIXTURES / "page_with_token.xml"
    data = path_file.read_bytes()
    result = count_records(data)
    assert result == 4


def test_check_oai_error():
    path_file_no_records = FIXTURES / "no_records_match.xml"
    data_err = path_file_no_records.read_bytes()

    path_file = FIXTURES / "page_with_token.xml"
    data = path_file.read_bytes()
    with pytest.raises(OAIError) as oai_err:
        check_oai_error(data_err)
    check_oai_error(data)
    assert oai_err.value.code == "noRecordsMatch"


def test_fetch_with_retry_does_not_retry_404():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError):
        fetch_with_retry(client, "https://fakeendpoint.com/oai", {}, backoff=0)

    assert len(requests) == 1


def test_fetch_with_retry_503():
    requests: list[httpx.Request] = []
    path_file = FIXTURES / "page_with_token.xml"
    data = path_file.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503)
        return httpx.Response(200, content=data)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = fetch_with_retry(client, "https://fakeendpoint.com/oai", {}, backoff=0)

    assert len(requests) == 2
    assert result == data


def test_fetch_with_retry_429():
    requests: list[httpx.Request] = []
    path_file = FIXTURES / "page_with_token.xml"
    data = path_file.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        if len(requests) == 2:
            return httpx.Response(429, headers={"Retry-After": "no float"})
        if len(requests) == 3:
            return httpx.Response(429)
        return httpx.Response(200, content=data)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    result = fetch_with_retry(
        client, "https://fakeendpoint.com/oai", {}, backoff=0, max_attempts=5
    )

    assert len(requests) == 4
    assert result == data


def test_fetch_with_retry_raise_max_attemp():
    requests: list[httpx.Request] = []
    path_file = FIXTURES / "page_with_token.xml"
    data = path_file.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) < 3:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, content=data)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError):
        fetch_with_retry(
            client, "https://fakeendpoint.com/oai", {}, backoff=0, max_attempts=1
        )


def test_harvest_no_records_match(tmp_path):
    path_file = FIXTURES / "no_records_match.xml"
    data = path_file.read_bytes()
    out_dir = tmp_path / "out"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, content=data)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    assert (
        harvest(
            client,
            "https://fakeendpoint.com/oai",
            metadata_prefix="oai_dc",
            set_spec="user-waterlat-gobacit",
            out_dir=out_dir,
            max_records=500,
            delay=0,
        )
        == 0
    )
    assert not out_dir.exists()


def test_harvest_bad_resumption_token(tmp_path):
    path = Path(tmp_path) / "page_001.xml"
    path.write_bytes(
        b"""
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
    <error code="badResumptionToken">The token is invalid</error></OAI-PMH>
    """
    )
    data = path.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, content=data)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(OAIError):
        harvest(
            client,
            "https://fakeendpoint.com/oai",
            metadata_prefix="oai_dc",
            set_spec="user-waterlat-gobacit",
            out_dir=tmp_path,
            max_records=500,
            delay=0,
        )


def test_harvest_invalid_xml(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"invalid xml")

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(HarvestError):
        harvest(
            client,
            "https://fakeendpoint.com/oai",
            metadata_prefix="oai_dc",
            set_spec="user-waterlat-gobacit",
            out_dir=tmp_path,
            max_records=500,
            delay=0,
        )


def test_harvest_transport_error(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.TransportError):
        harvest(
            client,
            "https://fakeendpoint.com/oai",
            metadata_prefix="oai_dc",
            set_spec="user-waterlat-gobacit",
            out_dir=tmp_path,
            max_records=500,
            delay=0,
        )


def test_paging(tmp_path):
    requests: list[httpx.Request] = []
    path_file_with_token = FIXTURES / "page_with_token.xml"
    data_with_token = path_file_with_token.read_bytes()

    path_file_without_token = FIXTURES / "last_page.xml"
    data_without_token = path_file_without_token.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if "resumptionToken" in request.url.params:
            return httpx.Response(200, content=data_without_token)
        return httpx.Response(200, content=data_with_token)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    total = harvest(
        client,
        "https://fakeendpoint.com/oai",
        metadata_prefix="oai_dc",
        set_spec="user-waterlat-gobacit",
        out_dir=tmp_path,
        max_records=500,
        delay=0,
    )
    records = count_records(data_with_token)
    records += count_records(data_without_token)
    assert total == records
    assert len(requests) == 2
    assert "metadataPrefix" in requests[0].url.params
    assert set(requests[1].url.params.keys()) == {"verb", "resumptionToken"}
    assert requests[1].url.params["resumptionToken"] == parse_resumption_token(
        data_with_token
    )
    assert len(list(tmp_path.iterdir())) == 2
