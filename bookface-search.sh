#!/bin/bash
# Bookface Search CLI - searches YC's internal Bookface forum via Algolia
# Usage: bookface-search.sh <query> [index] [hits_per_page]
#
# Indices: forum (default), companies, knowledge, deals, vendors, all
# Examples:
#   bookface-search.sh "best payment processor"
#   bookface-search.sh "stripe" companies
#   bookface-search.sh "hiring engineers" forum 10
#   bookface-search.sh "immigration lawyer" vendors
#   bookface-search.sh "fundraising" all 5
#
# Environment variables (or set in ~/.bookface_credentials):
#   BOOKFACE_USERNAME - your Bookface/YC username
#   BOOKFACE_PASSWORD - your Bookface/YC password

set -eo pipefail

QUERY="${1:?Usage: bookface-search.sh <query> [index] [hits_per_page]}"
INDEX_TYPE="${2:-forum}"
HITS="${3:-5}"

COOKIE_FILE="/tmp/bookface_cookies"
ALGOLIA_CACHE="/tmp/bookface_algolia_key"
BOOKFACE_URL="https://bookface.ycombinator.com"
YC_AUTH_URL="https://account.ycombinator.com"
CREDENTIALS_FILE="${BOOKFACE_CREDENTIALS_FILE:-$HOME/.bookface_credentials}"

# Load credentials from file if env vars not set
load_credentials() {
  if [[ -z "$BOOKFACE_USERNAME" || -z "$BOOKFACE_PASSWORD" ]]; then
    if [[ -f "$CREDENTIALS_FILE" ]]; then
      # shellcheck disable=SC1090
      source "$CREDENTIALS_FILE"
    fi
  fi

  if [[ -z "$BOOKFACE_USERNAME" || -z "$BOOKFACE_PASSWORD" ]]; then
    echo "ERROR: Bookface credentials not found." >&2
    echo "Set BOOKFACE_USERNAME and BOOKFACE_PASSWORD environment variables," >&2
    echo "or create $CREDENTIALS_FILE with:" >&2
    echo '  BOOKFACE_USERNAME="your_username"' >&2
    echo '  BOOKFACE_PASSWORD="your_password"' >&2
    return 1
  fi
}

# Map friendly names to Algolia index names
index_name_for() {
  case "$1" in
    forum) echo "Forum_production" ;;
    companies) echo "Company_production" ;;
    knowledge) echo "Knowledge_production" ;;
    deals) echo "Deal_production" ;;
    vendors) echo "Vendor_production" ;;
    articles) echo "Article_production" ;;
    *) echo "$1" ;;
  esac
}

get_algolia_credentials() {
  # Try cached credentials first (valid for ~12h)
  if [[ -f "$ALGOLIA_CACHE" ]] && [[ $(find "$ALGOLIA_CACHE" -mmin -720 2>/dev/null) ]]; then
    cat "$ALGOLIA_CACHE"
    return 0
  fi

  # Need to login and get fresh credentials
  load_credentials
  login_and_extract
}

login_and_extract() {
  # Step 1: Get CSRF token from auth page
  local auth_page
  auth_page=$(curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L \
    "${YC_AUTH_URL}/authenticate?continue=${BOOKFACE_URL}/" 2>/dev/null)

  local csrf_token
  csrf_token=$(echo "$auth_page" | grep -o 'csrf-token" content="[^"]*"' | head -1 | sed 's/csrf-token" content="//;s/"$//')

  if [[ -z "$csrf_token" ]]; then
    echo "ERROR: Could not get CSRF token" >&2
    return 1
  fi

  # Step 2: Login
  curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L \
    -X POST "${YC_AUTH_URL}/sign_in" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "X-CSRF-Token: ${csrf_token}" \
    --data-urlencode "ycid=${BOOKFACE_USERNAME}" \
    --data-urlencode "password=${BOOKFACE_PASSWORD}" \
    --data-urlencode "continue=${BOOKFACE_URL}/" \
    -o /dev/null 2>/dev/null

  # Step 3: Get Algolia credentials from the home page
  local home_page
  home_page=$(curl -s -c "$COOKIE_FILE" -b "$COOKIE_FILE" -L "${BOOKFACE_URL}/home" 2>/dev/null)

  local algolia_key
  algolia_key=$(echo "$home_page" | grep -o '"key":"[^"]*"' | head -1 | sed 's/"key":"//;s/"$//')
  local algolia_app
  algolia_app=$(echo "$home_page" | grep -o '"app":"[^"]*"' | head -1 | sed 's/"app":"//;s/"$//')

  if [[ -z "$algolia_key" || -z "$algolia_app" ]]; then
    echo "ERROR: Could not extract Algolia credentials. Login may have failed." >&2
    echo "Check your BOOKFACE_USERNAME and BOOKFACE_PASSWORD." >&2
    return 1
  fi

  # Cache the credentials
  echo "${algolia_app}|${algolia_key}" > "$ALGOLIA_CACHE"
  echo "${algolia_app}|${algolia_key}"
}

search_algolia() {
  local app_id="$1"
  local api_key="$2"
  local index_name="$3"
  local query="$4"
  local hits_per_page="$5"

  curl -s -X POST \
    "https://${app_id}-dsn.algolia.net/1/indexes/*/queries?x-algolia-application-id=${app_id}&x-algolia-api-key=${api_key}" \
    -H 'Content-Type: application/json' \
    -d "{\"requests\":[{\"indexName\":\"${index_name}\",\"params\":\"query=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")&hitsPerPage=${hits_per_page}\"}]}"
}

format_results() {
  local index_type="$1"
  python3 -c "
import sys, json

data = json.load(sys.stdin)
raw_results = data.get('results', [])
results = raw_results[0] if raw_results and isinstance(raw_results[0], dict) else {}
hits = results.get('hits', []) if isinstance(results, dict) else []
total = results.get('nbHits', 0)
index_type = '${index_type}'

if not hits:
    print('No results found.')
    sys.exit(0)

print(f'Found {total} results. Showing top {len(hits)}:')
print()

for i, hit in enumerate(hits, 1):
    if index_type == 'forum':
        title = hit.get('title') or hit.get('searchable_title', 'Untitled')
        body = (hit.get('body', '') or '')[:200]
        user = hit.get('user') or {}
        author = user.get('name', 'Unknown') if isinstance(user, dict) else 'Unknown'
        company_info = user.get('company') or {} if isinstance(user, dict) else {}
        company_info = company_info if isinstance(company_info, dict) else {}
        company = company_info.get('name', '')
        batches = ', '.join(company_info.get('batches', []))
        votes = hit.get('vote_count', 0)
        comments = hit.get('comment_count', 0)
        views = hit.get('views_count', 0)
        url = hit.get('url', hit.get('search_path', ''))
        channel = hit.get('channel', '')

        print(f'{i}. [{channel.upper()}] {title}')
        print(f'   Author: {author} ({company} {batches})')
        print(f'   Votes: {votes} | Comments: {comments} | Views: {views}')
        print(f'   URL: {url}')
        if body.strip():
            print(f'   Preview: {body.strip()[:150]}...')
        print()

    elif index_type == 'companies':
        name = hit.get('name', 'Unknown')
        one_liner = hit.get('one_liner', '')
        batch = hit.get('batch_display_name') or hit.get('batch', '')
        website = hit.get('website', '')
        team_size = hit.get('team_size', '')
        industry = hit.get('industry', '')
        status = hit.get('status', '')
        path = hit.get('search_path', '')

        print(f'{i}. {name} ({batch}) - {status}')
        print(f'   {one_liner}')
        print(f'   Industry: {industry} | Team: {team_size}')
        if website: print(f'   Website: {website}')
        print(f'   URL: {path}')
        print()

    elif index_type == 'knowledge':
        title = hit.get('title', 'Untitled')
        body = (hit.get('body', '') or '')[:200]
        parents = hit.get('parents', [])
        parents_str = ' -> '.join(p if isinstance(p, str) else str(p) for p in parents)
        path = hit.get('search_path', '')

        print(f'{i}. {title}')
        if parents_str: print(f'   Category: {parents_str}')
        print(f'   URL: {path}')
        if body.strip():
            print(f'   Preview: {body.strip()[:150]}...')
        print()

    elif index_type == 'deals':
        title = hit.get('title', 'Untitled')
        company = hit.get('company_name', '')
        details = (hit.get('details', '') or '')[:200]
        path = hit.get('search_path', '')
        rating = hit.get('weighted_rating', 0)

        print(f'{i}. {title} (by {company})')
        print(f'   Rating: {rating}')
        print(f'   URL: {path}')
        if details.strip():
            print(f'   Details: {details.strip()[:150]}...')
        print()

    elif index_type == 'vendors':
        title = hit.get('title', 'Untitled')
        company = hit.get('company_name', '')
        details = (hit.get('details', '') or '')[:200]
        tags = hit.get('vendor_tags', [])
        locations = hit.get('formatted_locations', [])

        print(f'{i}. {title} @ {company}')
        if tags: print(f'   Tags: {\", \".join(tags)}')
        if locations: print(f'   Locations: {\", \".join(locations)}')
        if details.strip():
            print(f'   Details: {details.strip()[:150]}...')
        print()

    elif index_type == 'articles':
        title = hit.get('title', 'Untitled')
        body = (hit.get('body', '') or '')[:200]
        parents = hit.get('parents', [])
        parents_str = ' -> '.join(p if isinstance(p, str) else str(p) for p in parents)
        path = hit.get('search_path', '')

        print(f'{i}. {title}')
        if parents_str: print(f'   Path: {parents_str}')
        print(f'   URL: {path}')
        if body.strip():
            print(f'   Preview: {body.strip()[:150]}...')
        print()

    else:
        print(f'{i}. {json.dumps(hit, indent=2)[:300]}')
        print()
"
}

# Main
credentials=$(get_algolia_credentials)
APP_ID=$(echo "$credentials" | cut -d'|' -f1)
API_KEY=$(echo "$credentials" | cut -d'|' -f2)

if [[ "$INDEX_TYPE" == "all" ]]; then
  for idx_type in forum knowledge companies vendors deals; do
    idx_name=$(index_name_for "$idx_type")
    echo "=========================================="
    echo "  SEARCHING: $(echo "$idx_type" | tr '[:lower:]' '[:upper:]')"
    echo "=========================================="
    search_algolia "$APP_ID" "$API_KEY" "$idx_name" "$QUERY" "$HITS" | format_results "$idx_type"
  done
else
  idx_name=$(index_name_for "$INDEX_TYPE")
  search_algolia "$APP_ID" "$API_KEY" "$idx_name" "$QUERY" "$HITS" | format_results "$INDEX_TYPE"
fi
