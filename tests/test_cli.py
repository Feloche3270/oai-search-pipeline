import shutil
from pathlib import Path
from typing import Any

import httpx
import pytest
from elasticsearch import Elasticsearch

from oaisearch.cli import main
from oaisearch.errors import EsConnectionError, OAIError
from oaisearch.models import Record, SearchResult

first_record = Record(
    identifier="oai:zenodo.org:4312898",
    title=(
        "Water politics, violence, and injustice: experiences from Brazil,"
        " Guatemala, and Mexico"
    ),
    source="fixtures",
    creators=["Castro, Jose Esteban"],
    publication_year=2020,
    doi="10.5281/zenodo.4312898",
)


def test_harvest_no_set():
    with pytest.raises(SystemExit):
        main(["harvest"])


def test_search_no_text():
    with pytest.raises(SystemExit):
        main(["search"])


def test_search_subject_subject_exact():
    with pytest.raises(SystemExit):
        main(["search", "water", "--subject", "Mexico", "--subject-exact", "sediment"])


# ----cmd_index----
def test_index_empty_folder(tmp_path, capsys):
    result = main(["index", "--folder", str(tmp_path)])

    assert result == 1
    assert "No records" in capsys.readouterr().err


def test_index_folder_one_fixture(tmp_path, capsys, monkeypatch):
    path = Path(__file__).parent / "fixtures/last_page.xml"
    path_tmp = tmp_path / "page_0001.xml"
    shutil.copyfile(path, path_tmp)

    def fake_get_client(url: str):
        raise EsConnectionError("Elasticsearch isn't running")

    monkeypatch.setattr("oaisearch.cli.get_client", fake_get_client)

    result = main(["index", "--folder", str(tmp_path)])

    assert result == 1
    assert "Elasticsearch isn't running" in capsys.readouterr().err


# ----cmd_harvest----
def test_harvest_return(capsys, monkeypatch):
    def fake_harvest(
        client: httpx.Client,
        endpoint: str,
        metadata_prefix: str,
        set_spec: str,
        out_dir: Path,
        max_records: int,
        delay: float = 1.0,
    ):
        return 32

    monkeypatch.setattr("oaisearch.cli.harvest", fake_harvest)

    result = main(["harvest", "--set", "user-fake"])

    assert result == 0
    assert "Harvested 32" in capsys.readouterr().out


def test_harvest_raise(capsys, monkeypatch):
    def fake_harvest(
        client: httpx.Client,
        endpoint: str,
        metadata_prefix: str,
        set_spec: str,
        out_dir: Path,
        max_records: int,
        delay: float = 1.0,
    ):
        raise OAIError("badArgument", "fake")

    monkeypatch.setattr("oaisearch.cli.harvest", fake_harvest)

    result = main(["harvest", "--set", "user-fake"])

    assert result == 1
    assert "fake" in capsys.readouterr().err


# ----cmd_search----
def test_search_no_result(capsys, monkeypatch):
    def fake_get_client(url: str):
        return url

    def fake_search(
        es: Elasticsearch, index: str, query: dict[str, Any], size: int = 10
    ):
        return (0, [])

    monkeypatch.setattr("oaisearch.cli.get_client", fake_get_client)
    monkeypatch.setattr("oaisearch.cli.search", fake_search)

    result = main(["search", "water"])

    assert result == 0
    assert "No results" in capsys.readouterr().out


def test_search_result(capsys, monkeypatch):
    def fake_get_client(url: str):
        return url

    def fake_search(
        es: Elasticsearch, index: str, query: dict[str, Any], size: int = 10
    ):
        return (1, [SearchResult(10.2456, first_record)])

    monkeypatch.setattr("oaisearch.cli.get_client", fake_get_client)
    monkeypatch.setattr("oaisearch.cli.search", fake_search)

    result = main(["search", "water"])

    assert result == 0
    assert "Water politics, violence, and injustice" in capsys.readouterr().out
