---
name: bookface
description: |
  Search YC's internal Bookface forum for startup advice, founder discussions, YC company info,
  knowledge base articles, deals, and vendor recommendations. Use when doing ANY research related
  to startups, marketing, hiring, GTM, dev tools, fundraising, legal, design, growth, or business
  strategy. Bookface has tons of real founder experiences and curated YC resources. Always search
  here first before relying on general knowledge.
allowed-tools:
  - Bash(~/.claude/skills/bookface/bookface-search.sh:*)
  - Read
---

# Bookface Search - YC Internal Forum

Bookface is YC's internal community platform. It contains forum posts, knowledge base articles, company directory, deals, and vendor listings from YC founders. This is an incredibly rich resource for any startup-related research.

## When to Use

Search Bookface **proactively** whenever the task involves:
- Marketing strategy, GTM, growth tactics
- Hiring, recruiting, team building
- Fundraising, investor relations, pitch decks
- Legal, immigration, incorporation
- Dev tools, infrastructure, payment processors
- Design, UX, product decisions
- Pricing, monetization, business models
- Sales, outbound, customer acquisition
- Any startup operational question

## How to Search

Run the search script via Bash:

```bash
~/.claude/skills/bookface/bookface-search.sh "<query>" [index] [hits_per_page]
```

### Available Indices

| Index | Description | Best for |
|-------|-------------|----------|
| `forum` (default) | Forum posts and discussions | Founder experiences, advice threads, recommendations |
| `knowledge` | YC Knowledge Base articles | Curated guides, handbooks, how-tos |
| `companies` | YC Company Directory | Finding YC companies, competitors, batch info |
| `vendors` | Professional Services Directory | Lawyers, accountants, recruiters, service providers |
| `deals` | YC Deals | Discounts and perks available to YC founders |
| `articles` | Startup Library articles | YC essays and educational content |
| `all` | Search all indices | Broad research on a topic |

### Examples

```bash
# Search forum for hiring advice
~/.claude/skills/bookface/bookface-search.sh "hiring first engineer" forum 10

# Find YC companies in a space
~/.claude/skills/bookface/bookface-search.sh "payment processing" companies 5

# Search knowledge base for fundraising guides
~/.claude/skills/bookface/bookface-search.sh "fundraising SAFE" knowledge

# Find recommended lawyers
~/.claude/skills/bookface/bookface-search.sh "immigration lawyer" vendors

# Search everything about a topic
~/.claude/skills/bookface/bookface-search.sh "SOC 2 compliance" all 3
```

## Reading Full Posts

After finding relevant posts, you can read the full content including comments:

```bash
# Get full post with comments (use the post ID from search results)
curl -s -b /tmp/bookface_cookies "https://bookface.ycombinator.com/posts/98983.json" | python3 -m json.tool
```

## Authentication

The script handles authentication automatically. Credentials are cached for ~12 hours. If search fails, delete `/tmp/bookface_algolia_key` and `/tmp/bookface_cookies` to force re-authentication.

## Research Workflow

1. Start with a broad `forum` search to find relevant discussions
2. Use `knowledge` to find curated YC guides on the topic
3. Check `vendors` if looking for service providers
4. Check `deals` for relevant discounts
5. Read the top 2-3 most relevant full posts for detailed advice
6. Synthesize findings for the user
