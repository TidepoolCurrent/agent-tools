#!/usr/bin/env python3
from activation import MemoryNetwork
from pathlib import Path

net = MemoryNetwork(str(Path("~/.openclaw/workspace/memory/memory-network.json").expanduser()))
print(f"Loaded: {len(net.nodes)} nodes")

# Show some nodes
for i, (mid, mem) in enumerate(list(net.nodes.items())[:3]):
    print(f"\nNode {i}:")
    print(f"  Schema: {mem.get('schema')}")
    header = mem.get("deviations", {}).get("header", "?")
    print(f"  Header: {header[:60]}")
    topic = mem.get("deviations", {}).get("topic", "none")
    print(f"  Topic: {topic}")

# Test retrieval
print("\n--- Testing cues ---")
for cue in ["memory", "moltbook", "build", "security", "research"]:
    results = net.retrieve(cue, top_k=3)
    print(f"\n'{cue}': {len(results)} results")
    for r in results:
        h = r.get("deviations", {}).get("header", "?")[:50]
        print(f"  [{r['activation']:.2f}] {h}")
