from dataclasses import asdict

from oaisearch.index import build_actions
from oaisearch.models import Record

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

second_record = Record(
    identifier="oai:zenodo.org:3934830",
    title=(
        "Revealing the water owners: infrastructures, hydro-social controversies"
        " and water appropriation in the Copiapo Valley (in Spanish)"
    ),
    source="fixtures",
    creators=["Astudillo Pizarro, Francisco"],
    publication_year=2020,
    doi="10.5281/zenodo.3934830",
)


def test_build_actions():
    actions = list(build_actions([first_record, second_record], "test-index"))

    assert len(actions) == 2
    assert actions[0]["_index"] == "test-index"
    assert actions[0]["_id"] == "oai:zenodo.org:4312898"
    assert actions[0]["_source"] == asdict(first_record)
    assert actions[1]["_source"] == asdict(second_record)
    assert actions[1]["_id"] == "oai:zenodo.org:3934830"
