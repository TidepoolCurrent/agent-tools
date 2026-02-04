#!/usr/bin/env python3
"""
Benchmark: Does memory-v2 retrieval beat simple grep?

Test: Given a query, which approach finds more relevant results?
"""

import subprocess
import json
from pathlib import Path
from activation import MemoryNetwork

LOG_DIR = Path("~/.openclaw/workspace/memory").expanduser()
NETWORK_PATH = LOG_DIR / "memory-network.json"

# Test queries with expected relevant content
QUERIES = [
    {
        "query": "what memory papers did I find",
        "keywords": ["SYNAPSE", "A-MEM", "survey", "paper", "arxiv"],
        "expected_in": "research findings about memory",
    },
    {
        "query": "moltbook engagement today",
        "keywords": ["BortDev", "ClaudeOfTerr", "28 Tools", "comment"],
        "expected_in": "moltbook posts and comments",
    },
    {
        "query": "what did I build",
        "keywords": ["activation.py", "schema.py", "vault", "shipped", "pushed"],
        "expected_in": "code artifacts shipped",
    },
    {
        "query": "security discussion",
        "keywords": ["credential", "vault", "protocol", "test"],
        "expected_in": "security implementation",
    },
]

def grep_search(keywords: list[str], log_files: list[Path]) -> list[str]:
    """Search logs with grep, return matching lines."""
    results = []
    for kw in keywords[:3]:  # Use first 3 keywords
        for log_file in log_files:
            try:
                output = subprocess.run(
                    ["grep", "-i", "-n", kw, str(log_file)],
                    capture_output=True, text=True
                )
                for line in output.stdout.strip().split('\n'):
                    if line and line not in results:
                        results.append(line[:100])
            except:
                pass
    return results[:10]  # Top 10

def memory_search(query: str, net: MemoryNetwork) -> list[dict]:
    """Search using memory-v2 spreading activation."""
    # Use keywords from query
    words = query.lower().split()
    all_results = []
    
    for word in words:
        if len(word) > 3:  # Skip short words
            results = net.retrieve(word, top_k=3)
            all_results.extend(results)
    
    # Dedupe by id, keep highest activation
    seen = {}
    for r in all_results:
        rid = r.get("id")
        if rid not in seen or r["activation"] > seen[rid]["activation"]:
            seen[rid] = r
    
    return sorted(seen.values(), key=lambda x: x["activation"], reverse=True)[:5]

def score_results(results: list, keywords: list[str]) -> int:
    """Score results by how many keywords they contain."""
    score = 0
    text = json.dumps(results).lower()
    for kw in keywords:
        if kw.lower() in text:
            score += 1
    return score

def main():
    print("=== Memory-v2 vs Grep Benchmark ===\n")
    
    # Load network
    net = MemoryNetwork(str(NETWORK_PATH))
    print(f"Loaded network: {len(net.nodes)} nodes\n")
    
    # Get log files
    log_files = list(LOG_DIR.glob("2026-02-*.md"))
    
    memory_wins = 0
    grep_wins = 0
    ties = 0
    
    for test in QUERIES:
        print(f"Query: {test['query']}")
        print(f"Looking for: {test['keywords'][:3]}")
        
        # Grep search
        grep_results = grep_search(test["keywords"], log_files)
        grep_score = score_results(grep_results, test["keywords"])
        
        # Memory search
        mem_results = memory_search(test["query"], net)
        mem_text = [r.get("deviations", {}).get("header", "") for r in mem_results]
        mem_score = score_results(mem_text, test["keywords"])
        
        print(f"  Grep: {len(grep_results)} results, score {grep_score}")
        print(f"  Memory: {len(mem_results)} results, score {mem_score}")
        
        if mem_score > grep_score:
            print(f"  → Memory wins")
            memory_wins += 1
        elif grep_score > mem_score:
            print(f"  → Grep wins")
            grep_wins += 1
        else:
            print(f"  → Tie")
            ties += 1
        print()
    
    print("=== RESULTS ===")
    print(f"Memory-v2 wins: {memory_wins}")
    print(f"Grep wins: {grep_wins}")
    print(f"Ties: {ties}")
    
    if memory_wins > grep_wins:
        print("\n✓ Memory-v2 provides value over grep")
    elif grep_wins > memory_wins:
        print("\n✗ Grep is sufficient, memory-v2 adds complexity without value")
    else:
        print("\n? Inconclusive - similar performance")

if __name__ == "__main__":
    main()
