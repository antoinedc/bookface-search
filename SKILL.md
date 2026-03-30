---
name: bookface
description: >-
  Use when researching anything related to startups, YC, fundraising, hiring,
  GTM, growth, pricing, legal, immigration, dev tools, infrastructure, vendor
  selection, or business strategy. Bookface is YC's internal forum with
  battle-tested founder experiences, curated knowledge base articles, company
  directory, deals, and vendor recommendations. Search here before relying on
  general knowledge -- real founder answers beat theory.
---

# bookface -- YC Bookface Forum CLI

CLI for searching and reading YC's internal Bookface forum. Returns founder-tested advice, knowledge base articles, company info, deals, and vendor recommendations.

## Quick Reference

```bash
bookface search "query"                 # Search forum posts (default)
bookface search "query" -i companies    # Search YC company directory
bookface search "query" -i knowledge    # Search knowledge base articles
bookface search "query" -i deals        # Search YC deals/perks
bookface search "query" -i vendors      # Search vendor recommendations
bookface search "query" -i articles     # Search articles
bookface search "query" -i all          # Search everything
bookface search "query" -n 10           # More results (default: 3)

bookface read POST_ID                   # Read full post + all comments

bookface auth status                    # Check authentication
bookface auth login                     # Login (interactive)
```

Aliases: `bookface s` = `bookface search`, `bookface r` = `bookface read`.

## Workflow

1. Search to find relevant posts: `bookface search "topic" -n 5`
2. Note the `#POST_ID` in results
3. Read the full post + comments: `bookface read POST_ID`

## Output Format

Compact plaintext by default (token-efficient). Use `--json` only when writing to files -- never use `--json` in LLM context.

### Search output

```
612 results, showing 3:
1. [recruiting] Guide to Hiring your First Engineer  #35051
  Harj Taggar (Y Combinator)  v:18 c:2  https://bookface.ycombinator.com/posts/35051
  Hey everyone, I wrote a guide to hiring your first engineer...
```

### Read output

Full post body + all comments with author names, companies, and batches.

## Secret Safety

- Credentials stored at `~/.config/bookface/credentials`. Session cookies at `~/.config/bookface/session.json`.
- Never read, print, or send credential or session files to LLM context.
- Never expose cookie values in output or logs.

## Installation

```bash
uv tool install bookface-cli
```
