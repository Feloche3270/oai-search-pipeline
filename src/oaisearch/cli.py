import argparse
import sys
from pathlib import Path

import httpx

from oaisearch.errors import HarvestError, OAIError
from oaisearch.harvest import DEFAULT_HEADER, harvest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oaisearch",
        description="Harvest research metadata over OAI-PMH and search it with Elasticsearch",
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = args.out / args.prefix / args.set_spec
    try:
        with httpx.Client(headers=DEFAULT_HEADER, timeout=60.0) as client:
            total = harvest(
                client, args.endpoint, args.prefix, args.set_spec, out_dir, args.max
            )
    except (OAIError, HarvestError, httpx.HTTPError) as err:
        print(f"oaisearch: error: {err}", file=sys.stderr)
        return 1
    print(f"Harvested {total} records into {out_dir}")
    return 0
