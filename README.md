# Bookface Search - Claude Code Skill

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that searches YC's internal [Bookface](https://bookface.ycombinator.com) forum. Gives your AI assistant access to thousands of YC founder discussions, knowledge base articles, company directory, deals, and vendor recommendations.

## Requirements

- A Bookface account (YC founders/alumni only)
- `curl` and `python3` (pre-installed on macOS/Linux)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## Installation

### 1. Clone the repo into your Claude Code skills directory

```bash
git clone https://github.com/antoinedc/bookface-search.git ~/.claude/skills/bookface
```

### 2. Make the script executable

```bash
chmod +x ~/.claude/skills/bookface/bookface-search.sh
```

### 3. Set up your credentials

Create a credentials file (this file is gitignored):

```bash
cat > ~/.bookface_credentials << 'EOF'
BOOKFACE_USERNAME="your_yc_username"
BOOKFACE_PASSWORD="your_yc_password"
EOF
chmod 600 ~/.bookface_credentials
```

Or set environment variables:

```bash
export BOOKFACE_USERNAME="your_yc_username"
export BOOKFACE_PASSWORD="your_yc_password"
```

### 4. Test it

```bash
~/.claude/skills/bookface/bookface-search.sh "best payment processor"
```

## Usage

```
bookface-search.sh <query> [index] [hits_per_page]
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

### Examples

```bash
# Search forum (default)
bookface-search.sh "hiring first engineer"

# Search specific index
bookface-search.sh "stripe" companies
bookface-search.sh "immigration lawyer" vendors
bookface-search.sh "fundraising SAFE" knowledge

# Control result count
bookface-search.sh "SOC 2 compliance" forum 10

# Search everything
bookface-search.sh "pricing strategy" all 3
```

### Reading Full Posts

After finding a relevant post, read the full content:

```bash
curl -s -b /tmp/bookface_cookies \
  "https://bookface.ycombinator.com/posts/POST_ID.json" \
  | python3 -m json.tool
```

## How It Works

1. Authenticates with Bookface via YC's SSO (credentials cached for ~12h)
2. Extracts session-scoped Algolia search credentials
3. Queries Algolia's search API directly (fast, no browser needed)
4. Formats results with titles, authors, vote counts, and preview text

## As a Claude Code Skill

Once installed, Claude Code will automatically detect the skill. When you're doing any research related to startups, marketing, hiring, GTM, fundraising, legal, or business strategy, Claude will search Bookface for relevant founder discussions and curated YC resources.

You can also invoke it directly with `/bookface`.

## Troubleshooting

**Authentication fails:**
```bash
rm /tmp/bookface_cookies /tmp/bookface_algolia_key
```
Then try again. This forces a fresh login.

**No results:**
- Check that your Bookface account has access to the content
- Try a different index (e.g., `knowledge` instead of `forum`)
- Use simpler search terms

## License

MIT
