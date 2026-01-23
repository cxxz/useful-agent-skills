#!/usr/bin/env python3
"""
Read webpage content with caching and LLM summary.

Default behavior: Show LLM summary
With --full-content: Show full webpage content

Examples:
  python scripts/read_webpage.py --url "https://example.com/article"
  python scripts/read_webpage.py --url "https://arxiv.org/html/2508.02994v1" --full-content
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from webcache_utils import (
    DEFAULT_WEBCACHE_FOLDER,
    create_meta_for_direct_access,
    get_content_path,
    get_latest_search_query,
    get_summary_path,
    get_webcache_path,
    load_meta,
    mark_content_fetched,
)


JINA_API_KEY = os.environ.get("JINA_API_KEY", "")
JINA_BASE_URL = os.environ.get("JINA_BASE_URL", "https://r.jina.ai")

SUMMARY_LLM_BASE_URL = os.environ.get(
    "SUMMARY_LLM_BASE_URL", "https://api.cerebras.ai/v1"
)
SUMMARY_LLM_MODEL_NAME = os.environ.get("SUMMARY_LLM_MODEL_NAME", "gpt-oss-120b")
SUMMARY_LLM_API_KEY = os.environ.get("SUMMARY_LLM_API_KEY", None)


def normalize_jina_url(url: str) -> str:
    if url.startswith("https://r.jina.ai/") and url.count("http") >= 2:
        return url[len("https://r.jina.ai/") :]
    return url


async def fetch_url_with_jina(url: str) -> Dict[str, Any]:
    """Fetch webpage content via Jina Reader."""
    if not url or not url.strip():
        return {"success": False, "content": "", "error": "URL cannot be empty"}

    if not JINA_API_KEY:
        return {
            "success": False,
            "content": "",
            "error": "JINA_API_KEY environment variable is not set",
        }

    url = normalize_jina_url(url)
    jina_url = f"{JINA_BASE_URL}/{url}"
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}

    retry_delays = [1, 2, 4]
    for attempt, delay in enumerate(retry_delays, 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    jina_url,
                    headers=headers,
                    timeout=httpx.Timeout(None, connect=20, read=60),
                    follow_redirects=True,
                )
            response.raise_for_status()
            content = response.text
            if not content:
                raise ValueError("No content returned from Jina Reader")
            return {"success": True, "content": content, "error": ""}
        except (httpx.HTTPError, ValueError) as exc:
            if attempt >= len(retry_delays):
                return {
                    "success": False,
                    "content": "",
                    "error": f"Jina Reader request failed: {exc}",
                }
            await asyncio.sleep(delay)

    return {"success": False, "content": "", "error": "Jina Reader request failed"}


async def generate_llm_summary(content: str) -> Dict[str, Any]:
    """Generate LLM summary of content."""
    if not content or not content.strip():
        return {"success": False, "summary": "", "error": "Content cannot be empty"}

    try:
        from openai import AsyncOpenAI
    except ImportError:
        return {
            "success": False,
            "summary": "",
            "error": "openai not installed. Run: pip install openai",
        }

    if not SUMMARY_LLM_BASE_URL or not SUMMARY_LLM_BASE_URL.strip():
        return {
            "success": False,
            "summary": "",
            "error": "SUMMARY_LLM_BASE_URL environment variable is not set",
        }

    base_url = SUMMARY_LLM_BASE_URL.rstrip("/")
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")].rstrip("/")

    api_key = SUMMARY_LLM_API_KEY or os.getenv("OPENAI_API_KEY", "")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    prompt = f"""
You are a helpful assistant that summarizes the content of a webpage concisely.
The content is:
<web_content>
{content}
</web_content>

ONLY output the summary, no other text.
"""

    retry_delays = [1, 2, 4]
    try:
        for attempt, delay in enumerate(retry_delays, 1):
            try:
                response = await client.chat.completions.create(
                    model=SUMMARY_LLM_MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                )
                summary = None
                if response and response.choices:
                    choice = response.choices[0]
                    summary = getattr(choice.message, "content", None) or getattr(
                        choice, "text", None
                    )
                if not summary:
                    raise ValueError("Unable to parse summary from LLM response")
                return {"success": True, "summary": summary, "error": ""}
            except Exception as exc:
                if attempt >= len(retry_delays):
                    return {
                        "success": False,
                        "summary": "",
                        "error": f"LLM summarization failed: {exc}",
                    }
                await asyncio.sleep(delay)
    finally:
        await client.close()

    return {"success": False, "summary": "", "error": "LLM summarization failed"}


def print_header(url: str, meta: Optional[Dict[str, Any]]) -> None:
    """Print the header with URL, title, and search query."""
    print(f"URL: {url}")
    if meta and meta.get("title"):
        print(f"Title: {meta['title']}")
    search_query = get_latest_search_query(meta) if meta else None
    if search_query:
        print(f"From search query: {search_query}")
    else:
        print("From search query: (direct access - no prior search)")


async def cmd_read(args: argparse.Namespace) -> int:
    """Main command to read webpage."""
    webcache_folder = Path(args.webcache_folder).resolve()
    url = args.url

    content_path = get_content_path(webcache_folder, url)
    summary_path = get_summary_path(webcache_folder, url)
    cache_folder = get_webcache_path(webcache_folder, url)

    # Load meta for display info
    meta = load_meta(webcache_folder, url)

    # Handle --full-content flag
    if args.full_content:
        # Check cache first
        if content_path.exists():
            content = content_path.read_text(encoding="utf-8")
            print_header(url, meta)
            print(f"\n=======Full content of the webpage=========")
            print(content)
            print(f"=======End of full content of the webpage=========")
            # print(f'\nThe full content of the webpage is saved to "{content_path}"')
            return 0

        # Fetch content
        fetch_result = await fetch_url_with_jina(url)
        if not fetch_result["success"]:
            print(f"Error: {fetch_result['error']}", file=sys.stderr)
            return 1

        content = fetch_result["content"]

        # Save content
        cache_folder.mkdir(parents=True, exist_ok=True)
        content_path.write_text(content, encoding="utf-8")

        # Create/update meta
        if not meta:
            create_meta_for_direct_access(webcache_folder, url)
        else:
            mark_content_fetched(webcache_folder, url)

        # Reload meta for display
        meta = load_meta(webcache_folder, url)

        print_header(url, meta)
        print(f"\n=======Full content of the webpage=========")
        print(content)
        print(f"=======End of full content of the webpage=========")
        print(f'\nThe full content of the webpage is saved to "{content_path}"')
        return 0

    # Default behavior: show summary
    content = None
    summary = None

    # Check if summary is cached
    if summary_path.exists():
        summary = summary_path.read_text(encoding="utf-8")
    else:
        # Need to get content first
        if content_path.exists():
            content = content_path.read_text(encoding="utf-8")
        else:
            # Fetch content
            fetch_result = await fetch_url_with_jina(url)
            if not fetch_result["success"]:
                print(f"Error: {fetch_result['error']}", file=sys.stderr)
                return 1

            content = fetch_result["content"]

            # Save content
            cache_folder.mkdir(parents=True, exist_ok=True)
            content_path.write_text(content, encoding="utf-8")

            # Create/update meta
            if not meta:
                create_meta_for_direct_access(webcache_folder, url)
                meta = load_meta(webcache_folder, url)
            else:
                mark_content_fetched(webcache_folder, url)

        # Generate summary
        summary_result = await generate_llm_summary(content)
        if not summary_result["success"]:
            print(f"Error: {summary_result['error']}", file=sys.stderr)
            return 1

        summary = summary_result["summary"]

        # Save summary
        summary_path.write_text(summary, encoding="utf-8")

    # Reload meta in case it was created during fetch
    if not meta:
        meta = load_meta(webcache_folder, url)

    # Display output
    print_header(url, meta)
    print(f"\n=======Summary of the webpage=========")
    print(summary)
    print(f"=======End of summary of the webpage=========")
    print(
        # f'\nThe full content of the webpage is saved to "{content_path}". '
        f'If you need detailed information about the webpage, rerun "read_webpage.py --url {url} --full-content" to display the full content.'
    )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read webpage content with caching and LLM summary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/read_webpage.py --url "https://example.com/article"
  python scripts/read_webpage.py --url "https://arxiv.org/html/2508.02994v1" --full-content
""",
    )
    parser.add_argument("--url", required=True, help="URL to read")
    parser.add_argument(
        "--full-content",
        action="store_true",
        help="Show full webpage content instead of summary",
    )
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
        exit_code = asyncio.run(cmd_read(args))
    except KeyboardInterrupt:
        print("\n\nCancelled by user.", file=sys.stderr)
        exit_code = 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
