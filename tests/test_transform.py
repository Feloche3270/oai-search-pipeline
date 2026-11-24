from pathlib import Path

from oaisearch.models import Record
from oaisearch.transform import clean_description, extract_doi, extract_year, parse_page


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
