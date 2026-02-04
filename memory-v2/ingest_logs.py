#!/usr/bin/env python3
"""
Ingest daily log files into memory-v2 network.
Test whether the system helps with real retrieval tasks.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from schema import encode_memory
from activation import MemoryNetwork

def parse_daily_log(filepath: Path) -> list[dict]:
    """Parse a daily log file into events."""
    events = []
    content = filepath.read_text()
    
    # Split by ## headers (sections)
    sections = re.split(r'\n## ', content)
    
    for section in sections[1:]:  # Skip first (before any ##)
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        header = lines[0].strip()
        body = '\n'.join(lines[1:]).strip()
        
        # Try to extract timestamp from header
        time_match = re.search(r'(\d{1,2}:\d{2})\s*(PST|UTC)?', header)
        timestamp = time_match.group(1) if time_match else None
        
        # Classify event type based on content
        event_type = classify_event(header, body)
        
        # Extract key details
        event = {
            "type": event_type,
            "header": header[:100],
            "timestamp": timestamp,
            "date": filepath.stem,  # e.g., "2026-02-04"
            "content_preview": body[:300] if body else "",
        }
        
        # Extract mentions of agents/people
        agents = re.findall(r'\*\*([A-Za-z_0-9]+)\*\*', body)
        if agents:
            event["mentions"] = agents[:5]  # Top 5
        
        # Extract key terms
        if "memory" in body.lower():
            event["topic"] = "memory"
        elif "moltbook" in body.lower():
            event["topic"] = "moltbook"
        elif "conservation" in body.lower() or "pycnopodia" in body.lower():
            event["topic"] = "conservation"
        elif "security" in body.lower() or "credential" in body.lower():
            event["topic"] = "security"
        
        events.append(event)
    
    return events

def classify_event(header: str, body: str) -> str:
    """Classify event type from content."""
    header_lower = header.lower()
    body_lower = body.lower()
    
    if "research" in header_lower or "papers" in body_lower:
        return "insight"
    elif "built" in header_lower or "shipped" in body_lower or "pushed" in body_lower:
        return "task"
    elif "post" in header_lower or "comment" in body_lower:
        return "engagement"
    elif "human" in header_lower or "directive" in body_lower:
        return "conversation"
    elif "critique" in header_lower or "doesn't hold" in body_lower:
        return "critique"
    else:
        return "insight"  # Default

def build_network_from_logs(log_dir: Path) -> MemoryNetwork:
    """Build memory network from all daily logs."""
    net = MemoryNetwork()
    
    log_files = sorted(log_dir.glob("2026-02-*.md"))
    print(f"Found {len(log_files)} log files")
    
    total_events = 0
    for log_file in log_files:
        events = parse_daily_log(log_file)
        print(f"  {log_file.name}: {len(events)} events")
        
        for event in events:
            encoded = encode_memory(event, event["type"])
            net.add(encoded)
            total_events += 1
    
    print(f"\nTotal: {total_events} events → {len(net.nodes)} nodes, {sum(len(v) for v in net.edges.values())} edges")
    return net

def test_retrieval(net: MemoryNetwork):
    """Test retrieval with real questions."""
    questions = [
        ("What did I build today?", ["task", "shipped", "built"]),
        ("Who engaged with my posts?", ["engagement", "moltbook", "comment"]),
        ("What memory research did I find?", ["memory", "paper", "research"]),
        ("What security work happened?", ["security", "credential", "vault"]),
        ("What conversations with human?", ["human", "directive", "conversation"]),
    ]
    
    print("\n=== RETRIEVAL TEST ===\n")
    
    for question, expected_terms in questions:
        print(f"Q: {question}")
        results = net.retrieve(question.split()[-1], top_k=3)  # Use last word as cue
        
        for r in results:
            header = r.get("core", {}).get("header", r.get("deviations", {}).get("header", "?"))
            print(f"  [{r['activation']:.2f}] {header[:60]}...")
        print()

if __name__ == "__main__":
    log_dir = Path("~/.openclaw/workspace/memory").expanduser()
    
    net = build_network_from_logs(log_dir)
    test_retrieval(net)
    
    # Save network for future use
    net.save(str(log_dir / "memory-network.json"))
    print(f"Saved network to {log_dir / 'memory-network.json'}")
