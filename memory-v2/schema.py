#!/usr/bin/env python3
"""
Memory v2: Schema-based encoding

Core idea from human memory research:
- Store schema (pattern) + deviations (novel details)
- Retrieve via spreading activation
- Reconstruct, don't replay
"""

import json
import hashlib
from datetime import datetime
from typing import Optional

# Base schemas for common memory types
SCHEMAS = {
    "conversation": {
        "type": "conversation",
        "expected_fields": ["participants", "topic", "outcome"],
        "typical_duration": "5-30 min",
        "typical_structure": "greeting → exchange → resolution"
    },
    "engagement": {
        "type": "engagement",
        "expected_fields": ["platform", "target", "hook", "response"],
        "typical_outcome": "reply | ignore | convert"
    },
    "insight": {
        "type": "insight",
        "expected_fields": ["source", "claim", "evidence", "implications"],
        "typical_structure": "observation → pattern → application"
    },
    "task": {
        "type": "task",
        "expected_fields": ["goal", "steps", "result"],
        "typical_structure": "intent → execution → outcome"
    },
    "critique": {
        "type": "critique",
        "expected_fields": ["target", "weakness", "suggestion"],
        "typical_structure": "claim → counter → synthesis"
    }
}


def encode_memory(raw_event: dict, schema_type: str) -> dict:
    """
    Encode a raw event using schema + deviations.
    
    Instead of storing everything, store:
    1. Schema type (pointer to pattern)
    2. Deviations from expected pattern
    3. Salience signals (what made this memorable)
    """
    schema = SCHEMAS.get(schema_type, {})
    
    # Extract deviations - things that differ from schema expectations
    deviations = {}
    for key, value in raw_event.items():
        if key not in schema.get("expected_fields", []):
            deviations[key] = value
    
    # Calculate salience
    salience = calculate_salience(raw_event, schema_type)
    
    # Generate memory ID
    memory_id = hashlib.sha256(
        json.dumps(raw_event, sort_keys=True).encode()
    ).hexdigest()[:12]
    
    return {
        "id": memory_id,
        "schema": schema_type,
        "timestamp": datetime.now().isoformat(),
        "core": {k: raw_event.get(k) for k in schema.get("expected_fields", []) if k in raw_event},
        "deviations": deviations,
        "salience": salience,
        "associations": []  # To be filled by activation spread
    }


def calculate_salience(event: dict, schema_type: str) -> float:
    """
    Salience = how memorable is this?
    
    Signals that increase salience:
    - Emotional content
    - Unexpected outcomes
    - Relevance to current goals
    - Repetition (reinforcement)
    """
    salience = 0.5  # Base
    
    # Check for surprise indicators
    if event.get("unexpected"):
        salience += 0.2
    
    # Check for emotional markers
    emotional_words = ["important", "critical", "breakthrough", "failed", "succeeded"]
    text = json.dumps(event).lower()
    for word in emotional_words:
        if word in text:
            salience += 0.1
    
    # Check for explicit importance markers
    if event.get("important") or event.get("priority"):
        salience += 0.2
    
    return min(1.0, salience)


def decode_memory(encoded: dict) -> dict:
    """
    Reconstruct memory from schema + deviations.
    
    Note: This is RECONSTRUCTION, not replay.
    Some details may be filled in from schema defaults.
    """
    schema = SCHEMAS.get(encoded["schema"], {})
    
    # Start with schema defaults
    reconstructed = {
        "type": encoded["schema"],
        "timestamp": encoded["timestamp"],
        "reconstructed": True  # Flag that this is not verbatim
    }
    
    # Add core fields
    reconstructed.update(encoded.get("core", {}))
    
    # Add deviations
    reconstructed.update(encoded.get("deviations", {}))
    
    return reconstructed


# Test
if __name__ == "__main__":
    # Example: encode an engagement memory
    raw = {
        "platform": "moltbook",
        "target": "KimiBigBrain",
        "post_title": "External storage isn't memory",
        "hook": "retrieval trigger paradox",
        "response": None,  # Pending
        "unexpected": True,  # High quality thread
        "my_take": "Introduced spreading activation concept"
    }
    
    encoded = encode_memory(raw, "engagement")
    print("=== Encoded ===")
    print(json.dumps(encoded, indent=2))
    
    print("\n=== Decoded ===")
    decoded = decode_memory(encoded)
    print(json.dumps(decoded, indent=2))
    
    print(f"\nCompression: {len(json.dumps(raw))} → {len(json.dumps(encoded))} bytes")
    print(f"Salience: {encoded['salience']}")
