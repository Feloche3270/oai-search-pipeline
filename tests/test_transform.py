import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from oaisearch.models import Record
from oaisearch.transform import (
    clean_description,
    extract_doi,
    extract_year,
    load_records,
    parse_page,
    parse_record,
)


def test_extract_year():
    list_years = ["unknown", "2019"]
    year = ["2026-11-24"]
    empty_years = []
    two_years = ["1900-11-24", "2026-11-24"]

    assert extract_year(list_years) == 2019
    assert extract_year(year) == 2026
    assert extract_year(empty_years) is None
    assert extract_year(two_years) == 1900


def test_extract_doi():
    doi = ["oai:zenodo.org:4313230", "https://doi.org/10.5281/zenodo.4313230"]
    no_doi = ["oai:zenodo.org:4313230", "imnotadoi"]

    assert extract_doi(doi) == "10.5281/zenodo.4313230"
    assert extract_doi(no_doi) is None


def test_clean_description():
    description = ["&lt;p&gt;Hello&lt;/p&gt;"]
    no_description = [""]

    assert clean_description(description) == "Hello"
    assert clean_description(no_description) is None


def test_parse_page():
    path = Path(__file__).parent / "fixtures/complete_and_missing_fields.xml"
    data = path.read_bytes()
    records = parse_page(data, "fixtures")
    assert records[0] == Record(
        identifier="oai:zenodo.org:4312898",
        title="Water politics, violence, and injustice: experiences from Brazil,"
        " Guatemala, and Mexico",
        source="fixtures",
        creators=[
            "Castro, Jose Esteban",
            "Kloster, Karina",
            "de Morais, Hugo Belarmino",
            "de Tavira, Ana Pohlenz",
            "Fracchia Figueiredo, Myriam",
            "Pelayo Pérez, Mariana Betzabeth",
        ],
        subjects=["infrastructures", "water politics", "water inequality"],
        publication_year=2020,
        description="This is the second issue developed by members of the "
        "WATERLAT-GOBACIT Network’s Thematic Area 10, Water and Violence.",
        doi="10.5281/zenodo.4312898",
        language="spa",
    )
    assert records[1] == Record(
        identifier="oai:zenodo.org:7508110",
        title="Administração de bens comuns: governança hídrica em disputa",
        source="fixtures",
    )


def test_load_records_with_data(tmp_path):
    path = Path(__file__).parent / "fixtures/complete_and_missing_fields.xml"
    path_tmp = tmp_path / "page_0001.xml"
    shutil.copyfile(path, path_tmp)

    assert len(load_records(tmp_path, "fixtures")) == 2


def test_load_record_without_data(tmp_path):
    assert len(load_records(tmp_path, "fixtures")) == 0


def test_parse_record_no_identifier():
    root_no_identifier = ET.fromstring(
        """
        <record xmlns="http://www.openarchives.org/OAI/2.0/">
            <header>
            </header>
            <metadata>
            <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
            </oai_dc:dc>
            </metadata>
        </record>
    """
    )
    assert parse_record(root_no_identifier, "tests") is None


def test_parse_record_identifier_no_text():
    root_identifier_no_text = ET.fromstring(
        """
        <record xmlns="http://www.openarchives.org/OAI/2.0/">
            <header>
            <identifier></identifier>
            </header>
            <metadata>
            <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
            </oai_dc:dc>
            </metadata>
        </record>
    """
    )
    assert parse_record(root_identifier_no_text, "tests") is None


def test_parse_record_no_metadata():
    root_no_metadata = ET.fromstring(
        """
        <record xmlns="http://www.openarchives.org/OAI/2.0/">
            <header>
            <identifier>oai:zenodo.org:4312898</identifier>
            </header>
        </record>
    """
    )
    assert parse_record(root_no_metadata, "tests") is None
