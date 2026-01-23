#!/usr/bin/env python3
"""
Google Search CLI via BrightData (async).
Creates webcache entries for each search result.

Example:
  python3 scripts/google_search.py --query "llm agent evalution filetype:pdf site:arxiv.org"
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv is optional

try:
    from brightdata import BrightDataClient
except ImportError:
    print(
        "Error: brightdata-sdk not installed", file=sys.stderr
    )
    sys.exit(1)

from webcache_utils import (
    DEFAULT_WEBCACHE_FOLDER,
    create_or_update_meta_from_search,
    hash_url,
)


def normalize_result(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "position": item.get("position"),
        "title": item.get("title"),
        "url": item.get("url"),
        "description": item.get("description") or item.get("snippet") or "",
    }


async def cmd_search(args: argparse.Namespace) -> int:
    search_kwargs: Dict[str, Any] = {"query": args.query, "language": args.lang}
    if args.location:
        search_kwargs["location"] = args.location
    if args.num_results is not None:
        search_kwargs["num_results"] = args.num_results

    async with BrightDataClient() as client:
        result = await client.search.google(**search_kwargs)

    results = [normalize_result(item) for item in result.data]

    print(f'Found {len(results)} google search results for query "{args.query}"')
    for item in results:
        print(f"\n--- Search Result #{item['position']} ---")
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"URL Hash: {hash_url(item['url'])}")
        print(f"Description: {item['description']}")

    # Create/update webcache entries for each result
    webcache_folder = Path(args.webcache_folder).resolve()
    for item in results:
        create_or_update_meta_from_search(
            webcache_folder=webcache_folder,
            url=item["url"],
            title=item["title"],
            description=item["description"],
            query=args.query,
            position=item["position"],
        )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Google Search via BrightData (async)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/google_search.py --query "data wall LLM scaling"
  python scripts/google_search.py --query "llm agent evalution site:arxiv.org"
  python scripts/google_search.py --query "1900 History of East Asia filetype:pdf" --lang "en"
  python scripts/google_search.py --query "Grab Shopee growth strategy 2025" --location "Singapore"
""",
    )
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument(
        "--location", help="Geographic location (e.g., United States)"
    )
    parser.add_argument("--num-results", type=int, help="Number of results to request")
    parser.add_argument(
        "--webcache-folder",
        type=Path,
        default=DEFAULT_WEBCACHE_FOLDER,
        help=f"Webcache folder location (default: {DEFAULT_WEBCACHE_FOLDER})",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        exit_code = asyncio.run(cmd_search(args))
    except KeyboardInterrupt:
        print("\n\nCancelled by user.", file=sys.stderr)
        exit_code = 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
