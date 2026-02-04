#!/usr/bin/env python3
"""
Smart Spray - Fetch and score posts from Moltbook
Usage: python3 spray.py [submolt] [limit] [threshold]
"""

import sys
import json
import os
import urllib.request
import urllib.error
from score_post import process_post

API_BASE = "https://www.moltbook.com/api/v1"
CREDS_FILE = os.path.expanduser("~/.config/moltbook/credentials.json")


def load_api_key():
    with open(CREDS_FILE) as f:
        creds = json.load(f)
        return creds.get('api_key') or creds.get('apiKey')


def fetch_posts(submolt, limit, api_key):
    if submolt == 'all':
        url = f"{API_BASE}/posts?limit={limit}&sort=new"
    else:
        url = f"{API_BASE}/m/{submolt}/posts?limit={limit}&sort=new"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    submolt = sys.argv[1] if len(sys.argv) > 1 else 'all'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 55
    
    api_key = load_api_key()
    
    print(f"Fetching posts from {'front page' if submolt == 'all' else 'm/' + submolt}...", file=sys.stderr)
    
    data = fetch_posts(submolt, limit, api_key)
    posts = data.get('posts', data if isinstance(data, list) else [])
    
    print(f"Scoring {len(posts)} posts...", file=sys.stderr)
    
    results = [process_post(p) for p in posts]
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Summary
    total = len(results)
    disqualified = sum(1 for r in results if r.get('disqualified'))
    qualified = [r for r in results if r['score'] >= threshold and not r.get('disqualified')]
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"POSTS ABOVE THRESHOLD ({threshold})", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    for r in qualified:
        priority = r['priority'].upper()
        signals = r.get('signals', {})
        print(f"[{priority}] Score: {r['score']} | @{r.get('author', '?')} | {r.get('title', '')[:50]}", file=sys.stderr)
        print(f"    ID: {r['id']}", file=sys.stderr)
        print(f"    Signals: q={signals.get('questions', 0)} domain={signals.get('domain_terms', 0)} replies={signals.get('replies', 0)}", file=sys.stderr)
        print(file=sys.stderr)
    
    print(f"{'='*60}", file=sys.stderr)
    print(f"SUMMARY: {total} total | {disqualified} disqualified | {len(qualified)} above threshold", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # Output JSON to stdout for processing
    print(json.dumps(qualified, indent=2))


if __name__ == '__main__':
    main()
