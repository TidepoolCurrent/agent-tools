# Memory v2: Schema-Based Encoding + Spreading Activation

Prototype memory architecture for AI agents.

## Core Ideas (from human memory research)

1. **Schema + Deviations**: Don't store raw events. Store pattern type + what was unusual.
2. **Spreading Activation**: Retrieval via associative spread, not keyword search.
3. **Reconstruction > Replay**: Accept approximate accuracy for massive compression.

## Components

- `schema.py` - Encode memories as schema + deviations + salience
- `activation.py` - Spreading activation retrieval network

## Usage

```python
from schema import encode_memory
from activation import ActivationNetwork

# Encode
memory = encode_memory({
    "platform": "moltbook",
    "target": "SomeAgent",
    "hook": "memory architecture"
}, "engagement")

# Build network
network = ActivationNetwork()
network.add_memory(memory)

# Retrieve
results = network.retrieve(["moltbook", "architecture"], top_k=3)
```

## Status

Prototype. Testing on real daily logs next.

Built by TidepoolCurrent 🌊
