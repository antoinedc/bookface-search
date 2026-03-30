"""Authentication: login, session persistence, cookie management."""
import json
import os
import sys
import time

import requests

from .config import (
    BOOKFACE_URL,
    BROWSER_HEADERS,
    CACHE_DIR,
    CONFIG_DIR,
    CREDENTIALS_FILE,
    SESSION_FILE,
    YC_AUTH_URL,
)


def _ensure_dirs():
    for d in (CONFIG_DIR, CACHE_DIR):
        os.makedirs(d, mode=0o700, exist_ok=True)


def _load_credentials():
    if not os.path.isfile(CREDENTIALS_FILE):
        return None, None
    env = {}
    with open(CREDENTIALS_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env.get("BOOKFACE_USERNAME"), env.get("BOOKFACE_PASSWORD")


def _save_session(session: requests.Session):
    """Persist session cookies to disk."""
    _ensure_dirs()
    data = {
        "cookies": {c.name: c.value for c in session.cookies},
        "saved_at": time.time(),
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)
    os.chmod(SESSION_FILE, 0o600)


def _load_session(session: requests.Session) -> bool:
    """Load persisted cookies into session. Returns True if loaded."""
    if not os.path.isfile(SESSION_FILE):
        return False
    try:
        with open(SESSION_FILE) as f:
            data = json.load(f)
        for name, value in data.get("cookies", {}).items():
            session.cookies.set(name, value)
        return True
    except (json.JSONDecodeError, KeyError):
        return False


def get_session() -> requests.Session:
    """Create a requests.Session with browser headers and persisted cookies."""
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    _load_session(s)
    return s


def _extract_csrf(html: str) -> str | None:
    import re
    m = re.search(r'csrf-token"\s+content="([^"]+)"', html)
    return m.group(1) if m else None


def login(session: requests.Session | None = None, quiet: bool = False) -> requests.Session:
    """Full login flow. Returns authenticated session."""
    _ensure_dirs()
    username, password = _load_credentials()
    if not username or not password:
        print(f"No credentials found. Create {CREDENTIALS_FILE} with:", file=sys.stderr)
        print(f'  BOOKFACE_USERNAME="you"', file=sys.stderr)
        print(f'  BOOKFACE_PASSWORD="pass"', file=sys.stderr)
        sys.exit(4)

    if session is None:
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)

    # Step 1: Get CSRF token from auth page
    auth_page = session.get(
        f"{YC_AUTH_URL}/authenticate",
        params={"continue": f"{BOOKFACE_URL}/"},
        headers={"Referer": f"{BOOKFACE_URL}/"},
    )
    csrf = _extract_csrf(auth_page.text)
    if not csrf:
        print("Failed to get CSRF token from YC auth page.", file=sys.stderr)
        sys.exit(1)

    # Step 2: POST login
    session.post(
        f"{YC_AUTH_URL}/sign_in",
        data={
            "ycid": username,
            "password": password,
            "continue": f"{BOOKFACE_URL}/",
        },
        headers={
            "Referer": f"{YC_AUTH_URL}/authenticate",
            "Origin": YC_AUTH_URL,
            "X-CSRF-Token": csrf,
            "Content-Type": "application/x-www-form-urlencoded",
            "Sec-Fetch-Site": "same-origin",
        },
        allow_redirects=True,
    )

    _save_session(session)
    if not quiet:
        print("Logged in.", file=sys.stderr)
    return session


def ensure_session() -> requests.Session:
    """Get an authenticated session, logging in only if necessary."""
    session = get_session()

    # Test if existing cookies work by hitting Bookface home
    if session.cookies:
        resp = session.get(
            f"{BOOKFACE_URL}/home",
            headers={"Referer": f"{BOOKFACE_URL}/"},
            allow_redirects=False,
        )
        if resp.status_code == 200:
            return session
        # Got redirected to login -- session expired

    return login(session, quiet=True)


def auth_status():
    """Print current auth status."""
    session = get_session()
    if not session.cookies:
        print("Not logged in.")
        return False

    resp = session.get(
        f"{BOOKFACE_URL}/home",
        headers={"Referer": f"{BOOKFACE_URL}/"},
        allow_redirects=False,
    )
    if resp.status_code == 200:
        print("Authenticated.")
        return True
    else:
        print("Session expired.")
        return False
