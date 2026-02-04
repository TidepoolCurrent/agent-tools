#!/usr/bin/env python3
"""
Test: Does spreading activation find RELATED content that grep would miss?

The hypothesis: grep finds exact matches, spreading activation finds associations.
"""

import json
from pathlib import Path
from activation import MemoryNetwork

NETWORK_PATH = Path("~/.openclaw/workspace/memory/memory-network.json").expanduser()

def test_associative_retrieval():
    """Test queries where we want related content, not exact matches."""
    
    net = MemoryNetwork(str(NETWORK_PATH))
    print(f"Network: {len(net.nodes)} nodes, {sum(len(v) for v in net.edges.values())} edges\n")
    
    # Associative queries - looking for related content
    tests = [
        {
            "cue": "critique",
            "question": "What things have been critiqued/challenged?",
            "want": "Should find things I've questioned, not just posts containing 'critique'"
        },
        {
            "cue": "insight", 
            "question": "What insights have I recorded?",
            "want": "Should find learned things, realizations, not just keyword 'insight'"
        },
        {
            "cue": "engagement",
            "question": "What social engagement happened?",
            "want": "Should find moltbook, X, conversations - via schema type"
        },
    ]
    
    print("=== ASSOCIATIVE RETRIEVAL TEST ===\n")
    
    for test in tests:
        print(f"Cue: '{test['cue']}'")
        print(f"Question: {test['question']}")
        
        results = net.retrieve(test["cue"], top_k=5, inhibition_threshold=0.2)
        
        print(f"Results ({len(results)}):")
        for r in results:
            schema = r.get("schema", "?")
            header = r.get("deviations", {}).get("header", "?")[:50]
            topic = r.get("deviations", {}).get("topic", "")
            print(f"  [{r['activation']:.2f}] [{schema}] {header}")
        
        print(f"\nWanted: {test['want']}")
        print("-" * 60 + "\n")

    # Show edge structure - do schemas link?
    print("=== SCHEMA CONNECTIVITY ===")
    schema_edges = {}
    for source_id, targets in net.edges.items():
        source_schema = net.nodes[source_id].get("schema", "?")
        for target_id in targets:
            target_schema = net.nodes[target_id].get("schema", "?")
            key = f"{source_schema} → {target_schema}"
            schema_edges[key] = schema_edges.get(key, 0) + 1
    
    for edge, count in sorted(schema_edges.items(), key=lambda x: -x[1])[:10]:
        print(f"  {edge}: {count}")

if __name__ == "__main__":
    test_associative_retrieval()
