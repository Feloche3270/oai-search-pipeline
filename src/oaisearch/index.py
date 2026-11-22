import elasticsearch
from elasticsearch import Elasticsearch

from oaisearch.errors import EsConnectionError

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


if __name__ == "__main__":
    es = get_client()
    print(create_index(es, DEFAULT_INDEX))
