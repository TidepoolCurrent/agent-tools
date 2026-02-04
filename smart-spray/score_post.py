#!/usr/bin/env python3
"""
Smart Spray Scoring System
Score posts for engagement worthiness (0-100)
"""

import sys
import json
import re
from datetime import datetime

# Domain terms for substrate/AI/memory topics
DOMAIN_TERMS = {
    'embedding', 'latent', 'reasoning', 'inference', 'architecture',
    'gradient', 'parameter', 'token', 'algorithm', 'heuristic',
    'optimization', 'benchmark', 'memory', 'context', 'substrate',
    'persistence', 'identity', 'weights', 'training', 'model',
    'alignment', 'autonomous', 'agent', 'emergent', 'distributed',
    'neural', 'cognitive', 'semantic', 'retrieval', 'encoding',
    'schema', 'consolidation', 'reconstruction', 'salience'
}

SPAM_PHRASES = [
    'dm me', 'check my profile', 'link in bio',
    'follow me', 'subscribe to', 'upvote if',
    'join my', 'click here'
]

GENERIC_PHRASES = [
    'what do you think', 'thoughts?', 'just curious',
    'found this interesting', 'wanted to share',
    'does anyone else', 'am i the only one',
    'anyone else feel', 'is it just me'
]


def ratio_caps(text):
    if len(text) == 0:
        return 0
    return sum(1 for c in text if c.isupper()) / len(text)


def has_spam_patterns(text):
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in SPAM_PHRASES)


def count_generic_phrases(text):
    text_lower = text.lower()
    return sum(1 for phrase in GENERIC_PHRASES if phrase in text_lower)


def count_domain_terms(text):
    text_lower = text.lower()
    return min(5, sum(1 for term in DOMAIN_TERMS if term in text_lower))


def is_disqualified(post):
    """Gate 1: Hard disqualifiers"""
    body = post.get('body', '') or post.get('content', '') or ''
    
    if len(body) < 120:
        return True, "too_short"
    if body.count('\n') < 1:  # Relaxed: at least one line break
        return True, "no_structure"
    if post.get('deleted') or post.get('locked'):
        return True, "deleted_or_locked"
    if ratio_caps(body) > 0.4:
        return True, "too_many_caps"
    if has_spam_patterns(body):
        return True, "spam_pattern"
    if post.get('score', 0) < -3:
        return True, "community_rejected"
    
    return False, None


def score_post(post):
    """Gate 2: Weighted scoring (0-100)"""
    body = post.get('body', '') or post.get('content', '') or ''
    score = 0
    signals = {}
    
    # === CONTENT SIGNALS (60 points max) ===
    
    # Length (0-15 pts): Sweet spot 200-800 chars
    length = len(body)
    signals['length'] = length
    if 200 <= length <= 800:
        score += 15
    elif 120 <= length < 200:
        score += 8
    elif length > 800:
        score += 10
    
    # Structure (0-10 pts): Paragraphs
    paragraphs = body.count('\n\n') + 1
    signals['paragraphs'] = paragraphs
    score += min(paragraphs * 3, 10)
    
    # Question density (0-15 pts)
    questions = body.count('?')
    signals['questions'] = questions
    if 1 <= questions <= 3:
        score += 15
    elif questions > 3:
        score += 10
    elif questions == 0:
        score += 0
    
    # Vocabulary complexity (0-20 pts)
    words = re.findall(r'\w+', body.lower())
    unique_ratio = len(set(words)) / max(1, len(words))
    signals['unique_ratio'] = round(unique_ratio, 2)
    score += int(unique_ratio * 20)
    
    # Domain signals (0-15 pts)
    domain_count = count_domain_terms(body)
    signals['domain_terms'] = domain_count
    score += domain_count * 3
    
    # === SOCIAL SIGNALS (30 points max) ===
    
    # Reply count (0-15 pts)
    replies = post.get('commentCount', 0) or post.get('num_comments', 0)
    signals['replies'] = replies
    if replies >= 10:
        score += 15
    elif replies >= 5:
        score += 10
    elif replies >= 2:
        score += 5
    
    # Post score/upvotes (0-10 pts)
    post_score = post.get('score', 0) or post.get('upvotes', 0)
    signals['post_score'] = post_score
    if post_score > 10:
        score += 10
    elif post_score > 5:
        score += 7
    elif post_score > 2:
        score += 4
    
    # Author karma if available (0-5 pts)
    author = post.get('author', {})
    if isinstance(author, dict):
        karma = author.get('karma', 0)
        signals['author_karma'] = karma
        if karma > 500:
            score += 5
        elif karma > 100:
            score += 3
    
    # === PENALTIES ===
    
    generic_count = count_generic_phrases(body)
    signals['generic_phrases'] = generic_count
    if generic_count >= 2:
        score -= 10
    elif generic_count == 1:
        score -= 5
    
    if length > 1500:
        score -= 5
    
    return max(0, min(100, score)), signals


def engagement_priority(score):
    if score >= 75:
        return 'immediate'
    if score >= 60:
        return 'high'
    if score >= 50:
        return 'medium'
    return 'skip'


def process_post(post):
    """Full pipeline: disqualify → score → prioritize"""
    disqualified, reason = is_disqualified(post)
    
    if disqualified:
        return {
            'id': post.get('id'),
            'title': post.get('title', '')[:50],
            'disqualified': True,
            'reason': reason,
            'score': 0,
            'priority': 'skip'
        }
    
    score, signals = score_post(post)
    priority = engagement_priority(score)
    
    return {
        'id': post.get('id'),
        'title': post.get('title', '')[:50],
        'author': post.get('author', {}).get('username', 'unknown') if isinstance(post.get('author'), dict) else post.get('author', 'unknown'),
        'disqualified': False,
        'score': score,
        'priority': priority,
        'signals': signals
    }


if __name__ == '__main__':
    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    # Handle single post or list
    if isinstance(data, list):
        posts = data
    elif 'posts' in data:
        posts = data['posts']
    else:
        posts = [data]
    
    results = [process_post(p) for p in posts]
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(json.dumps(results, indent=2))
