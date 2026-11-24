from oaisearch.models import Record, SearchResult
from oaisearch.search import build_query, format_result

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
    identifier="oai:zenodo.org:4312898",
    title=(
        "Water politics, violence, and injustice: experiences from Brazil,"
        " Guatemala, and Mexico"
    ),
    source="fixtures",
    creators=["Castro, Jose Esteban", "Kloster, Karina"],
)

third_record = Record(
    identifier="oai:zenodo.org:4312898",
    title=(
        "Water politics, violence, and injustice: experiences from Brazil,"
        " Guatemala, and Mexico"
    ),
    source="fixtures",
    creators=["Castro, Jose Esteban", "Kloster, Karina", "de Morais, Hugo Belarmino"],
)

fourth_record = Record(
    identifier="oai:zenodo.org:4312898",
    title=(
        "Water politics, violence, and injustice: experiences from Brazil,"
        " Guatemala, and Mexico"
    ),
    source="fixtures",
    language="spa",
)


def test_build_query():
    simple_query = build_query("river")
    query_with_year = build_query("river", from_year=2020)
    query_all_words = build_query("river", all_words=True)
    subject_exact_query = build_query("river", subject_exact="sediment")
    subject_query = build_query("river", subject="sediment")
    language_query = build_query("river", language="spa")

    assert simple_query["bool"]["filter"] == []
    assert query_with_year["bool"]["filter"] == [
        {"range": {"publication_year": {"gte": 2020}}}
    ]
    assert "operator" in query_all_words["bool"]["must"][0]["multi_match"]
    assert (
        "minimum_should_match" not in query_all_words["bool"]["must"][0]["multi_match"]
    )
    assert subject_exact_query["bool"]["filter"] == [
        {"term": {"subjects.keyword": "sediment"}}
    ]
    assert subject_query["bool"]["filter"] == [{"match": {"subjects": "sediment"}}]
    assert language_query["bool"]["filter"] == [{"term": {"language": "spa"}}]


def test_format_result():
    text_first_record = format_result(
        1, SearchResult(score=10.256, record=first_record)
    )
    text_second_record = format_result(
        2, SearchResult(score=9.355654, record=second_record)
    )
    text_third_record = format_result(3, SearchResult(score=6.0, record=third_record))
    text_fourth_record = format_result(4, SearchResult(score=0.0, record=fourth_record))

    assert "et al." not in text_second_record
    assert "Kloster, Karina" in text_second_record
    assert "et al." in text_third_record
    assert "de Morais" not in text_third_record
    assert "2020" in text_first_record
    assert "10.5281/zenodo.4312898" in text_first_record
    assert "Unknown creators" in text_fourth_record
    assert "spa" in text_fourth_record
