"""Read full posts and comments from Bookface."""
import json
import sys

from .auth import ensure_session
from .config import BOOKFACE_URL


def _fetch_post(session, post_id: str) -> dict:
    resp = session.get(
        f"{BOOKFACE_URL}/posts/{post_id}.json",
        headers={
            "Accept": "application/json",
            "Referer": f"{BOOKFACE_URL}/",
        },
    )
    if resp.status_code == 404:
        print(f"Post {post_id} not found.", file=sys.stderr)
        sys.exit(5)
    resp.raise_for_status()
    return resp.json()


def _fetch_comments(session, post_id: str) -> list:
    resp = session.get(
        f"{BOOKFACE_URL}/posts/{post_id}/comments.json",
        headers={
            "Accept": "application/json",
            "Referer": f"{BOOKFACE_URL}/posts/{post_id}",
        },
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else data.get("comments", [])


def _author_line(user: dict) -> str:
    name = user.get("full_name") or user.get("name", "?")
    # Post author uses nested company dict, comment author uses companies list
    companies = user.get("companies", [])
    if companies and isinstance(companies, list):
        co = companies[0] if isinstance(companies[0], dict) else {}
        company = co.get("name", "")
        batches = ", ".join(co.get("batches", []))
    else:
        co = user.get("company") or {}
        co = co if isinstance(co, dict) else {}
        company = co.get("name", "")
        batches = ", ".join(co.get("batches", []))
    origin = f"{company} {batches}".strip()
    return f"{name} ({origin})" if origin else name


def _fmt_comments(comments: list, depth: int = 0) -> list[str]:
    lines = []
    indent = "  " * depth
    for c in comments:
        if c.get("deleted"):
            continue
        user = c.get("user", {})
        author = _author_line(user)
        ts = (c.get("created_at") or "")[:10]
        body = c.get("body", "")
        lines.append(f"{indent}{author}  {ts}")
        for bline in body.split("\n"):
            lines.append(f"{indent}  {bline}")
        children = c.get("comments", [])
        if children:
            lines.extend(_fmt_comments(children, depth + 1))
    return lines


def read_post(post_id: str, as_json: bool = False):
    session = ensure_session()
    post_data = _fetch_post(session, post_id)
    comments = _fetch_comments(session, post_id)

    post = post_data.get("post", {})

    if as_json:
        post["_comments"] = comments
        json.dump(post, sys.stdout, indent=2)
        print()
        return

    # Header
    title = post.get("title", "?")
    user = post.get("user") or {}
    author = _author_line(user)
    ts = (post.get("created_at") or "")[:10]
    votes = post.get("vote_info", {}).get("count", 0)
    views = post.get("views_count", 0)
    comment_count = post.get("comment_count", 0)
    channel = post.get("channel", "")
    url = f"{BOOKFACE_URL}/posts/{post_id}"

    print(title)
    ch_prefix = f"[{channel}] " if channel else ""
    print(f"{ch_prefix}{author}  {ts}  v:{votes} views:{views} c:{comment_count}")
    print(url)
    print()

    # Full body
    body = post.get("body", "")
    if body:
        print(body)

    # Comments
    if comments:
        print()
        print(f"--- {len(comments)} comments ---")
        for line in _fmt_comments(comments):
            print(line)
