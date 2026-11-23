from typing import Any

from elasticsearch import Elasticsearch

from oaisearch.models import Record, SearchResult

SEARCH_FIELD = ["title^4", "subjects^3", "creators^1", "description^1"]


def build_query(
    text: str,
    from_year: int | None = None,
    subject: str | None = None,
    subject_exact: str | None = None,
    language: str | None = None,
    all_words: bool = False,
) -> dict[str, Any]:
    text_query: dict[str, Any] = {
        "multi_match": {"query": text, "fields": SEARCH_FIELD}
    }
    if all_words:
        text_query["multi_match"]["operator"] = "and"
    else:
        text_query["multi_match"]["minimum_should_match"] = "67%"

    filters: list[dict[str, Any]] = []
    if from_year is not None:
        filters.append({"range": {"publication_year": {"gte": from_year}}})
    if subject is not None:
        filters.append({"match": {"subjects": subject}})
    if subject_exact is not None:
        filters.append({"term": {"subjects.keyword": subject_exact}})
    if language is not None:
        filters.append({"term": {"language": language}})

    return {"bool": {"must": [text_query], "filter": filters}}


def search(
    es: Elasticsearch, index: str, query: dict[str, Any], size: int = 10
) -> tuple[int, list[SearchResult]]:
    search_results: list[SearchResult] = []
    response = es.search(index=index, query=query, size=size)
    for hit in response["hits"]["hits"]:
        search_result = SearchResult(
            score=float(hit["_score"]), record=Record(**hit["_source"])
        )
        search_results.append(search_result)
    return (response["hits"]["total"]["value"], search_results)


def format_result(rank: int, result: SearchResult) -> str:
    creators = ";".join(result.record.creators[:2])
    lang = "No lang"
    publication_year = "Unknown publication year"
    doi = "Unknown DOI"
    if len(result.record.creators) > 2:
        creators += " et al."
    elif len(creators) == 0:
        creators = "Unknown creators"
    if result.record.language is not None:
        lang = result.record.language
    if result.record.publication_year is not None:
        publication_year = str(result.record.publication_year)
    if result.record.doi is not None:
        doi = result.record.doi
    message = f"{rank}. [{result.score:.4f}] {result.record.title}"
    message += f"({publication_year})\n{creators} - {lang} - {doi}"
    return message
