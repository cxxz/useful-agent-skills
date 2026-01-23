#!/usr/bin/env python3
"""
Shared webcache utilities for web-search skill.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Default webcache location relative to scripts folder
# Resolves to: /lustre/xuco/workspace/llm/ib360/webcache/
DEFAULT_WEBCACHE_FOLDER = Path(__file__).parent.parent.parent.parent.parent / "webcache"


def hash_url(url: str) -> str:
    """Generate a 16-character hash from a URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def get_webcache_path(webcache_folder: Path, url: str) -> Path:
    """Get the webcache folder path for a given URL."""
    return webcache_folder / hash_url(url)


def get_meta_path(webcache_folder: Path, url: str) -> Path:
    """Get the meta.json path for a given URL."""
    return get_webcache_path(webcache_folder, url) / "meta.json"


def get_content_path(webcache_folder: Path, url: str) -> Path:
    """Get the full_content.md path for a given URL."""
    return get_webcache_path(webcache_folder, url) / "full_content.md"


def get_summary_path(webcache_folder: Path, url: str) -> Path:
    """Get the llm_summary.md path for a given URL."""
    return get_webcache_path(webcache_folder, url) / "llm_summary.md"


def load_meta(webcache_folder: Path, url: str) -> Optional[Dict[str, Any]]:
    """Load meta.json for a URL if it exists."""
    meta_path = get_meta_path(webcache_folder, url)
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return None


def save_meta(webcache_folder: Path, url: str, meta: Dict[str, Any]) -> Path:
    """Save meta.json for a URL, creating directory if needed."""
    cache_path = get_webcache_path(webcache_folder, url)
    cache_path.mkdir(parents=True, exist_ok=True)
    meta_path = cache_path / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta_path


def create_or_update_meta_from_search(
    webcache_folder: Path,
    url: str,
    title: str,
    description: str,
    query: str,
    position: int,
) -> Dict[str, Any]:
    """
    Create or update meta.json from a search result.
    Appends to searches array if query is new, updates if existing.
    """
    now = datetime.now(timezone.utc).isoformat()
    url_hash = hash_url(url)

    existing_meta = load_meta(webcache_folder, url)

    if existing_meta:
        meta = existing_meta
        # Update title/description with latest
        meta["title"] = title
        meta["description"] = description
        meta["last_updated"] = now

        # Check if this query already exists
        query_found = False
        for search in meta["searches"]:
            if search["query"] == query:
                search["timestamp"] = now
                search["position"] = position
                query_found = True
                break

        if not query_found:
            meta["searches"].append(
                {"query": query, "timestamp": now, "position": position}
            )
    else:
        meta = {
            "url": url,
            "url_hash": url_hash,
            "title": title,
            "description": description,
            "searches": [{"query": query, "timestamp": now, "position": position}],
            "content_fetched": False,
            "content_fetched_at": None,
            "last_updated": now,
        }

    save_meta(webcache_folder, url, meta)
    return meta


def create_meta_for_direct_access(webcache_folder: Path, url: str) -> Dict[str, Any]:
    """
    Create minimal meta.json when URL is accessed directly without prior search.
    """
    now = datetime.now(timezone.utc).isoformat()
    url_hash = hash_url(url)

    meta = {
        "url": url,
        "url_hash": url_hash,
        "title": None,
        "description": None,
        "searches": [],
        "content_fetched": True,
        "content_fetched_at": now,
        "last_updated": now,
    }

    save_meta(webcache_folder, url, meta)
    return meta


def mark_content_fetched(webcache_folder: Path, url: str) -> None:
    """Update meta.json to mark content as fetched."""
    meta = load_meta(webcache_folder, url)
    if meta:
        now = datetime.now(timezone.utc).isoformat()
        meta["content_fetched"] = True
        meta["content_fetched_at"] = now
        meta["last_updated"] = now
        save_meta(webcache_folder, url, meta)


def get_latest_search_query(meta: Dict[str, Any]) -> Optional[str]:
    """Get the most recent search query from meta, or None if no searches."""
    if not meta or not meta.get("searches"):
        return None
    # Sort by timestamp descending and get first
    searches = sorted(meta["searches"], key=lambda x: x["timestamp"], reverse=True)
    return searches[0]["query"] if searches else None
