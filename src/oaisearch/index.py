from collections.abc import Iterator
from dataclasses import asdict
from typing import Any
from pathlib import Path

import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from oaisearch.errors import EsConnectionError
from oaisearch.models import Record
from oaisearch.transform import load_records

DEFAULT_ES_URL = "http://localhost:9200"
DEFAULT_INDEX = "records"
SETTINGS = {"number_of_shards": 1, "number_of_replicas": 0}
MAPPINGS = {
    "properties": {
        "identifier": {"type": "keyword"},
        "title": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
        },
        "source": {"type": "keyword"},
        "creators": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
        },
        "subjects": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
        },
        "publication_year": {"type": "integer"},
        "description": {"type": "text"},
        "doi": {"type": "keyword"},
        "language": {"type": "keyword"},
    }
}


def get_client(url: str = DEFAULT_ES_URL) -> Elasticsearch:
    es = Elasticsearch(url)
    try:
        es.info()
    except elasticsearch.ConnectionError:
        raise EsConnectionError("Elasticsearch isn't running") from None
    return es


def create_index(es: Elasticsearch, index: str) -> bool:
    if es.indices.exists(index=index):
        return False
    es.indices.create(index=index, settings=SETTINGS, mappings=MAPPINGS)
    return True


def build_actions(records: list[Record], index: str) -> Iterator[dict[str, Any]]:
    for record in records:
        document = asdict(record)
        yield {"_index": index, "_id": record.identifier, "_source": document}


def count_documents(es: Elasticsearch, index: str) -> int:
    response = es.count(index=index)
    count = int(response["count"])
    return count


def index_records(es: Elasticsearch, index: str, records: list[Record]) -> int:
    actions = build_actions(records, index)
    successes, _ = bulk(es, actions, raise_on_error=True)
    es.indices.refresh(index=index)
    return successes
