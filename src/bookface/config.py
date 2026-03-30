"""Paths, constants, and browser headers."""
import os

CONFIG_DIR = os.path.expanduser("~/.config/bookface")
CACHE_DIR = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")) + "/bookface"
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
ALGOLIA_CACHE_FILE = os.path.join(CACHE_DIR, "algolia.json")

BOOKFACE_URL = "https://bookface.ycombinator.com"
YC_AUTH_URL = "https://account.ycombinator.com"

ALGOLIA_CACHE_TTL_HOURS = 12

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-CH-UA": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_EMPTY = 3
EXIT_AUTH = 4
EXIT_NOT_FOUND = 5
