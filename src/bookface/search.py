"""Algolia-based search for Bookface content."""
import json
import os
import re
import sys
import time
import urllib.parse

import requests

from .auth import ensure_session
from .config import (
    ALGOLIA_CACHE_FILE,
    ALGOLIA_CACHE_TTL_HOURS,
    BOOKFACE_URL,
    BROWSER_HEADERS,
    CACHE_DIR,
)

INDEX_MAP = {
    "forum": "Forum_production",
    "companies": "Company_production",
    "knowledge": "Knowledge_production",
    "deals": "Deal_production",
    "vendors": "Vendor_production",
    "articles": "Article_production",
}


def _load_algolia_cache():
    if not os.path.isfile(ALGOLIA_CACHE_FILE):
        return None
    try:
        with open(ALGOLIA_CACHE_FILE) as f:
            data = json.load(f)
        age_hours = (time.time() - data.get("saved_at", 0)) / 3600
        if age_hours < ALGOLIA_CACHE_TTL_HOURS:
            return data["app_id"], data["api_key"]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _save_algolia_cache(app_id: str, api_key: str):
    os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
    with open(ALGOLIA_CACHE_FILE, "w") as f:
        json.dump({"app_id": app_id, "api_key": api_key, "saved_at": time.time()}, f)
    os.chmod(ALGOLIA_CACHE_FILE, 0o600)


def _extract_algolia_creds(html: str):
    app_match = re.search(r'"app":"([^"]+)"', html)
    key_match = re.search(r'"key":"([^"]+)"', html)
    if app_match and key_match:
        return app_match.group(1), key_match.group(1)
    return None, None


def _get_algolia_credentials() -> tuple[str, str]:
    # Try cache first
    cached = _load_algolia_cache()
    if cached:
        return cached

    # Need to fetch from Bookface home page (with existing session -- no re-login)
    session = ensure_session()
    resp = session.get(
        f"{BOOKFACE_URL}/home",
        headers={"Referer": f"{BOOKFACE_URL}/"},
    )
    app_id, api_key = _extract_algolia_creds(resp.text)
    if not app_id or not api_key:
        print("Failed to extract Algolia credentials from Bookface.", file=sys.stderr)
        sys.exit(1)

    _save_algolia_cache(app_id, api_key)
    return app_id, api_key


def _query_algolia(app_id: str, api_key: str, index: str, query: str, hits: int) -> dict:
    url = f"https://{app_id}-dsn.algolia.net/1/indexes/*/queries"
    resp = requests.post(
        url,
        params={"x-algolia-application-id": app_id, "x-algolia-api-key": api_key},
        json={"requests": [{"indexName": index, "params": f"query={urllib.parse.quote(query)}&hitsPerPage={hits}"}]},
        headers={
            "Content-Type": "application/json",
            "User-Agent": BROWSER_HEADERS["User-Agent"],
            "Referer": f"{BOOKFACE_URL}/",
            "Origin": BOOKFACE_URL,
        },
    )
    resp.raise_for_status()
    return resp.json()


def _fmt_forum(hit: dict) -> str:
    title = hit.get("title") or hit.get("searchable_title", "Untitled")
    user = hit.get("user") or {}
    author = user.get("name", "?") if isinstance(user, dict) else "?"
    co = (user.get("company") or {}) if isinstance(user, dict) else {}
    co = co if isinstance(co, dict) else {}
    company = co.get("name", "")
    batches = ", ".join(co.get("batches", []))
    origin = f"{company} {batches}".strip()
    v = hit.get("vote_count", 0)
    c = hit.get("comment_count", 0)
    ch = hit.get("channel", "")
    url = hit.get("url", hit.get("search_path", ""))
    # Extract post ID from URL for easy `bookface read` usage
    post_id = ""
    if "/posts/" in str(url):
        parts = str(url).split("/posts/")
        if len(parts) > 1:
            post_id = parts[1].split("#")[0].split("/")[0]
    id_hint = f"  #{post_id}" if post_id else ""
    body = (hit.get("body", "") or "").replace("\n", " ")[:120].strip()
    lines = [f"[{ch}] {title}{id_hint}", f"  {author} ({origin})  v:{v} c:{c}  {url}"]
    if body:
        lines.append(f"  {body}")
    return "\n".join(lines)


def _fmt_company(hit: dict) -> str:
    name = hit.get("name", "?")
    batch = hit.get("batch_display_name") or hit.get("batch", "")
    liner = hit.get("one_liner", "")
    status = hit.get("status", "")
    path = hit.get("search_path", "")
    return f"{name} ({batch}) {status}\n  {liner}  {path}"


def _fmt_knowledge(hit: dict) -> str:
    title = hit.get("title", "Untitled")
    parents = hit.get("parents", [])
    cat = " > ".join(str(p) for p in parents)
    path = hit.get("search_path", "")
    body = (hit.get("body", "") or "").replace("\n", " ")[:120].strip()
    lines = [title, f"  {cat}  {path}" if cat else f"  {path}"]
    if body:
        lines.append(f"  {body}")
    return "\n".join(lines)


def _fmt_deal(hit: dict) -> str:
    title = hit.get("title", "Untitled")
    company = hit.get("company_name", "")
    path = hit.get("search_path", "")
    rating = hit.get("weighted_rating", 0)
    return f"{title} ({company}) rating:{rating}  {path}"


def _fmt_vendor(hit: dict) -> str:
    title = hit.get("title", "Untitled")
    company = hit.get("company_name", "")
    tags = ", ".join(hit.get("vendor_tags", []))
    return f"{title} @ {company}  [{tags}]"


FORMATTERS = {
    "forum": _fmt_forum,
    "companies": _fmt_company,
    "knowledge": _fmt_knowledge,
    "articles": _fmt_knowledge,
    "deals": _fmt_deal,
    "vendors": _fmt_vendor,
}


def search(query: str, index_type: str = "forum", hits: int = 5, as_json: bool = False):
    app_id, api_key = _get_algolia_credentials()

    if index_type == "all":
        indices = ["forum", "knowledge", "companies", "vendors", "deals"]
    else:
        indices = [index_type]

    all_results = []

    for idx in indices:
        algolia_index = INDEX_MAP.get(idx, idx)
        data = _query_algolia(app_id, api_key, algolia_index, query, hits)
        results = data.get("results", [{}])[0] if data.get("results") else {}
        result_hits = results.get("hits", [])
        total = results.get("nbHits", 0)

        if as_json:
            all_results.append({"index": idx, "total": total, "hits": result_hits})
            continue

        if len(indices) > 1:
            print(f"--- {idx} ---")

        if not result_hits:
            print("No results.")
            continue

        print(f"{total} results, showing {len(result_hits)}:")
        fmt = FORMATTERS.get(idx, lambda h: h.get("title", "?"))
        for i, hit in enumerate(result_hits, 1):
            print(f"{i}. {fmt(hit)}")

    if as_json:
        json.dump(all_results, sys.stdout, indent=2)
        print()
