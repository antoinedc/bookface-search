#!/usr/bin/env python3
"""bookface -- CLI for YC's Bookface forum."""
import argparse
import sys

from . import __version__


def main():
    p = argparse.ArgumentParser(
        prog="bookface",
        description="Search and read YC's Bookface forum.",
    )
    p.add_argument("--version", action="version", version=f"bookface {__version__}")
    sub = p.add_subparsers(dest="command")

    # auth
    auth_p = sub.add_parser("auth", help="Authentication management")
    auth_sub = auth_p.add_subparsers(dest="auth_command")
    auth_sub.add_parser("login", help="Login and persist session")
    auth_sub.add_parser("status", help="Check session status")
    auth_sub.add_parser("logout", help="Clear session")

    # search
    search_p = sub.add_parser("search", aliases=["s"], help="Search Bookface")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument(
        "-i", "--index",
        default="forum",
        choices=["forum", "companies", "knowledge", "deals", "vendors", "articles", "all"],
        help="Index to search (default: forum)",
    )
    search_p.add_argument("-n", "--hits", type=int, default=5, help="Number of results")
    search_p.add_argument("--json", action="store_true", help="JSON output")

    # read
    read_p = sub.add_parser("read", aliases=["r"], help="Read a post with comments")
    read_p.add_argument("post_id", help="Post ID (number from URL)")
    read_p.add_argument("--json", action="store_true", help="JSON output")

    args = p.parse_args()

    if not args.command:
        p.print_help()
        sys.exit(2)

    if args.command == "auth":
        from .auth import auth_status, login
        import os
        from .config import SESSION_FILE

        if args.auth_command == "login":
            login()
        elif args.auth_command == "status":
            ok = auth_status()
            sys.exit(0 if ok else 4)
        elif args.auth_command == "logout":
            if os.path.isfile(SESSION_FILE):
                os.unlink(SESSION_FILE)
                print("Session cleared.")
            else:
                print("No session to clear.")
        else:
            auth_p.print_help()
            sys.exit(2)

    elif args.command in ("search", "s"):
        from .search import search
        search(args.query, args.index, args.hits, as_json=args.json)

    elif args.command in ("read", "r"):
        from .read import read_post
        read_post(args.post_id, as_json=args.json)


if __name__ == "__main__":
    main()
