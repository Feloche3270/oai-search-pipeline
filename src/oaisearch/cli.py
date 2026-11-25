import argparse
import sys
from pathlib import Path

import elasticsearch
import httpx

from oaisearch.errors import EsConnectionError, HarvestError, OAIError
from oaisearch.harvest import DEFAULT_HEADER, harvest
from oaisearch.index import count_documents, create_index, get_client, index_records
from oaisearch.search import build_query, format_result, search
from oaisearch.transform import load_records


def cmd_harvest(args: argparse.Namespace) -> int:
    try:
        out_dir = args.out / args.prefix / args.set_spec
        with httpx.Client(headers=DEFAULT_HEADER, timeout=60.0) as client:
            total = harvest(
                client, args.endpoint, args.prefix, args.set_spec, out_dir, args.max
            )
    except (OAIError, HarvestError, httpx.HTTPError) as err:
        print(f"oaisearch: error: {err}", file=sys.stderr)
        return 1
    print(f"Harvested {total} records into {out_dir}")
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    try:
        records = load_records(args.folder, args.source)
        if not records:
            print(f"No records found in {args.folder}", file=sys.stderr)
            return 1
        es = get_client(args.es_url)
        index = create_index(es, args.index)
        indexed_records = index_records(es, args.index, records)
        count = count_documents(es, args.index)
    except (EsConnectionError, elasticsearch.ApiError) as err:
        print(f"oaisearch: error: {err}", file=sys.stderr)
        return 1
    if index:
        print(f"Created index '{args.index}'")
    else:
        print(f"Index '{args.index}' already exists")
    print(
        f"Indexed {indexed_records} records into '{args.index}'"
        + f" ({count} documents in index)"
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    try:
        es = get_client(args.es_url)
        query = build_query(
            text=args.text,
            from_year=args.from_year,
            subject=args.subject,
            subject_exact=args.subject_exact,
            language=args.language,
            all_words=args.all_words,
        )
        total, hits = search(es, args.index, query, args.size)
    except (EsConnectionError, elasticsearch.ApiError) as err:
        print(f"oaisearch: error: {err}", file=sys.stderr)
        return 1
    if not hits:
        print(f'No results for "{args.text}"')
        return 0
    print(f"Found {total} results, showing {len(hits)}")
    for rank, hit in enumerate(hits, start=1):
        result = format_result(rank, hit)
        print(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oaisearch",
        description="Harvest research metadata over OAI-PMH and "
        "search it with Elasticsearch",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    harvest_parser = subparsers.add_parser("harvest", help="Harvest data")
    harvest_parser.add_argument(
        "--endpoint",
        type=str,
        default="https://zenodo.org/oai2d",
        help="OAI-PMH base URL (default: Zenodo)",
    )
    harvest_parser.add_argument(
        "--prefix",
        type=str,
        default="oai_dc",
        help="Metadata format, e.g. oai_dc or oai_datacite",
    )
    harvest_parser.add_argument(
        "--set",
        type=str,
        required=True,
        help="OAI set spec, e.g. user-<community> on Zenodo",
        dest="set_spec",
    )
    harvest_parser.add_argument(
        "--max",
        type=int,
        default=500,
        help="Maximum records to harvest (rounded up to whole pages)",
    )
    harvest_parser.add_argument(
        "--out", type=Path, default=Path("data"), help="Output folder for raw XML pages"
    )
    harvest_parser.set_defaults(func=cmd_harvest)

    index_parser = subparsers.add_parser("index", help="Index data")
    index_parser.add_argument(
        "--folder",
        type=Path,
        required=True,
        help="Folder of harvested XML pages, e.g. data/oai_dc/<set>",
    )
    index_parser.add_argument(
        "--source",
        type=str,
        default="zenodo",
        help="Repository name stored with each record (default: zenodo)",
    )
    index_parser.add_argument(
        "--index", type=str, default="records", help="Elasticsearch index name"
    )
    index_parser.add_argument(
        "--es-url",
        type=str,
        default="http://localhost:9200",
        help="Elasticsearch URL",
        dest="es_url",
    )
    index_parser.set_defaults(func=cmd_index)

    search_parser = subparsers.add_parser("search", help="Search data")
    search_parser.add_argument("text", type=str, help="Words to search for")
    search_parser.add_argument(
        "--from-year",
        type=int,
        help="Only records published in or after this year",
        dest="from_year",
    )
    exclusive_group = search_parser.add_mutually_exclusive_group()
    exclusive_group.add_argument(
        "--subject", type=str, help="Filter on a subject (tolerant match)"
    )
    exclusive_group.add_argument(
        "--subject-exact",
        type=str,
        help="Filter on an exact subject (case-sensitive)",
        dest="subject_exact",
    )
    search_parser.add_argument(
        "--language", type=str, help="Filter on a language code, e.g. spa"
    )
    search_parser.add_argument(
        "--all-words",
        action="store_true",
        help="Require all words, in any order (default: 67%% of them)",
    )
    search_parser.add_argument(
        "--size", type=int, default=10, help="Number of results to show (default: 10)"
    )
    search_parser.add_argument(
        "--index", type=str, default="records", help="Elasticsearch index name"
    )
    search_parser.add_argument(
        "--es-url",
        type=str,
        default="http://localhost:9200",
        help="Elasticsearch URL",
        dest="es_url",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "harvest":
        return cmd_harvest(args)
    elif args.command == "index":
        return cmd_index(args)
    elif args.command == "search":
        return cmd_search(args)
    return 0
