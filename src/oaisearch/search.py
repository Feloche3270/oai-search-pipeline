from typing import Any

SEARCH_FIELD = ["title^4", "subject^3", "creators^1", "description^1"]


def build_query(
    text: str,
    from_year: int | None = None,
    subject: str | None = None,
    subject_exact: str | None = None,
    language: str | None = None,
    all_words: bool = False,
) -> dict[str, Any]:
    text_query = {"multi_match": {"query": text, "fields": SEARCH_FIELD}}
    if all_words is True:
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


if __name__ == "__main__":
    print(build_query("river sediment", from_year=2020, language="spa"))