# Bookface CLI

A CLI for searching and reading YC's internal [Bookface](https://bookface.ycombinator.com) forum. Works standalone or as a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill.

Gives your AI assistant (or you) access to thousands of YC founder discussions, knowledge base articles, company directory, deals, and vendor recommendations.

## Requirements

- A Bookface account (YC founders/alumni only)
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

```bash
uv tool install bookface-cli
```

Or from source:

```bash
git clone https://github.com/antoinedc/bookface-search.git
cd bookface-search
uv tool install -e .
```

## Usage

```bash
# Search forum posts (default)
bookface search "hiring first engineer"

# Search specific index
bookface search "stripe" -i companies
bookface search "immigration lawyer" -i vendors
bookface search "fundraising SAFE" -i knowledge
bookface search "SOC 2 compliance" -i deals
bookface search "pricing strategy" -i all

# Control result count
bookface search "hiring" -n 10

# Read full post with comments
bookface read POST_ID

# JSON output (for piping to files)
bookface search "query" --json
```

### Search Indices

| Index | Description |
|-------|-------------|
| `forum` (default) | Forum posts and discussions |
| `knowledge` | YC Knowledge Base articles |
| `companies` | YC Company Directory |
| `vendors` | Professional Services Directory |
| `deals` | YC Deals and perks |
| `articles` | Startup Library articles |
| `all` | Search all indices at once |

### Aliases

`bookface s` = `bookface search`, `bookface r` = `bookface read`.

## Authentication

```bash
bookface auth login     # Interactive login
bookface auth status    # Check auth state
```

Credentials are stored at `~/.config/bookface/credentials`. Session cookies are cached at `~/.config/bookface/session.json` and refresh automatically.

## As a Claude Code Skill

Install the skill:

```bash
git clone https://github.com/antoinedc/bookface-search.git ~/.claude/skills/bookface
```

Claude Code will automatically detect the `SKILL.md` and use Bookface when researching startup topics -- marketing, hiring, GTM, fundraising, legal, pricing, vendor selection, and more.

## How It Works

1. Authenticates with Bookface via YC's SSO
2. Extracts session-scoped Algolia search credentials
3. Queries Algolia's search API directly (fast, no browser needed)
4. Formats results with titles, authors, vote counts, and preview text

## Troubleshooting

**Authentication fails:**
```bash
rm -rf ~/.config/bookface/session.json
bookface auth login
```

**No results:**
- Check that your Bookface account has access to the content
- Try a different index (e.g., `knowledge` instead of `forum`)
- Use simpler search terms

## License

MIT
