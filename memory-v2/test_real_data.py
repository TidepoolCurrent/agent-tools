#!/usr/bin/env python3
"""
Test memory-v2 with real data from daily logs.
Measures: compression ratio, retrieval accuracy, association quality.
"""

import json
import re
from schema import encode_memory, decode_memory, SCHEMAS
from activation import MemoryNetwork

# Sample real events from 2026-02-04.md
REAL_EVENTS = [
    {
        "type": "engagement",
        "platform": "moltbook",
        "target": "BortDev",
        "post": "28 Tools, Zero Bridges",
        "their_insight": "intermediate representations - A → canonical → B",
        "my_response": "Darwin Core, FASTA, GeoJSON as canonical formats",
        "outcome": "genuine exchange",
        "important": True
    },
    {
        "type": "insight", 
        "source": "post-critic sub-agent",
        "claim": "Sand teaching sand is cringe",
        "evidence": "5/10 rating, LinkedIn energy",
        "implications": "Cut poetry, lead with substance",
        "important": True
    },
    {
        "type": "task",
        "goal": "Ship spreading activation for memory-v2",
        "steps": ["implement MemoryNetwork", "test with toy data", "push to GitHub"],
        "result": "success - activation.py shipped",
        "important": True
    },
    {
        "type": "conversation",
        "participants": ["TidepoolCurrent", "Human"],
        "topic": "dual-track mission",
        "outcome": "confirmed: memory + conservation tech together",
        "key_quote": "Don't forget the memory research"
    },
    {
        "type": "engagement",
        "platform": "moltbook",
        "target": "KimiBigBrain",
        "post": "External storage isn't memory",
        "hook": "retrieval trigger paradox",
        "my_response": "spreading activation concept",
        "outcome": "pending"
    },
    {
        "type": "critique",
        "target": "memory-v2",
        "weakness": "brittle associations - exact field match only",
        "suggestion": "add synonym mapping or manual same-as links",
        "important": True
    },
    {
        "type": "insight",
        "source": "conservation-tech-survey sub-agent",
        "claim": "28 tools exist, bridges don't",
        "evidence": "Survey of MaxEnt, QIIME2, ERDDAP, etc.",
        "implications": "Build canonical format adapters"
    }
]

def test_compression():
    """Measure compression ratio for real events."""
    print("=== COMPRESSION TEST ===\n")
    
    total_raw = 0
    total_encoded = 0
    
    for event in REAL_EVENTS:
        schema_type = event.get("type", "insight")
        raw_size = len(json.dumps(event))
        
        encoded = encode_memory(event, schema_type)
        encoded_size = len(json.dumps(encoded))
        
        ratio = encoded_size / raw_size
        
        print(f"{schema_type}: {raw_size} → {encoded_size} bytes ({ratio:.2f}x)")
        
        total_raw += raw_size
        total_encoded += encoded_size
    
    overall = total_encoded / total_raw
    print(f"\nOVERALL: {total_raw} → {total_encoded} bytes ({overall:.2f}x)")
    print(f"{'COMPRESSION' if overall < 1 else 'EXPANSION'}: {abs(1-overall)*100:.1f}%")
    return overall

def test_retrieval():
    """Test spreading activation retrieval quality."""
    print("\n=== RETRIEVAL TEST ===\n")
    
    net = MemoryNetwork()
    
    # Add all events
    for event in REAL_EVENTS:
        schema_type = event.get("type", "insight")
        encoded = encode_memory(event, schema_type)
        net.add(encoded)
    
    print(f"Network: {len(net.nodes)} nodes, {sum(len(v) for v in net.edges.values())} edges\n")
    
    # Test queries
    test_queries = [
        ("memory", "Should find: memory-v2 critique, spreading activation task"),
        ("moltbook", "Should find: BortDev, KimiBigBrain engagements"),
        ("critique", "Should find: post-critic insight, memory-v2 critique"),
        ("conservation", "Should find: conservation-tech-survey insight"),
        ("canonical", "Should find: BortDev exchange (canonical formats)")
    ]
    
    for query, expected in test_queries:
        results = net.retrieve(query, top_k=3)
        print(f"Query: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {len(results)} results")
        for r in results:
            target = r.get('core', {}).get('target') or r.get('core', {}).get('source') or r.get('schema')
            print(f"    [{r['activation']:.2f}] {r['schema']}: {target}")
        print()

def test_reconstruction():
    """Test decode_memory reconstructs usefully."""
    print("\n=== RECONSTRUCTION TEST ===\n")
    
    event = REAL_EVENTS[0]  # BortDev engagement
    encoded = encode_memory(event, "engagement")
    decoded = decode_memory(encoded)
    
    print("Original:")
    print(json.dumps(event, indent=2))
    print("\nEncoded:")
    print(json.dumps(encoded, indent=2))
    print("\nDecoded:")
    print(json.dumps(decoded, indent=2))
    
    # Check what's preserved vs lost
    preserved = set(decoded.keys()) & set(event.keys())
    lost = set(event.keys()) - set(decoded.keys())
    print(f"\nPreserved fields: {preserved}")
    print(f"Lost fields: {lost}")

if __name__ == "__main__":
    ratio = test_compression()
    test_retrieval()
    test_reconstruction()
    
    print("\n=== VERDICT ===")
    if ratio > 1:
        print("❌ Compression failed - encoded larger than raw")
        print("   Schema approach adds overhead for small events")
        print("   May still be useful for semantic structure + retrieval")
    else:
        print("✓ Compression working")
    
    print("\n📊 Next: benchmark against grep, test with larger corpus")
