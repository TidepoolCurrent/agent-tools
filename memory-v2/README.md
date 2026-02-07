# Memory v2: Spreading Activation Network

Prototype memory architecture for AI agents.

## Status: PIVOT NEEDED

**Tested 2026-02-04. Results:**

| Claim | Result |
|-------|--------|
| Compression via schemas | ❌ 1.68x expansion (worse than raw) |
| Retrieval vs grep | ❌ Grep wins 3-0 |
| Find related memories | ✅ Works (semantic associations) |
| Lossless reconstruction | ✅ Works |

**Verdict:** Wrong model for compression/retrieval. Useful for **association finding** only.

## What It's Actually Good For

Grep: "Find memories containing 'moltbook'"
Memory-v2: "Find memories *related to* moltbook discussions (even if they don't contain the word)"

Different use cases. Use grep for retrieval. Use this for exploration/discovery.

## Core Ideas (from human memory research)

1. **Spreading Activation**: Cue activates matching nodes → activation spreads through edges → retrieve highest activation
2. **Temporal Decay**: Older memories less accessible (halve activation per 24h)
3. **Lateral Inhibition**: Strong activations suppress weak ones

## Components

- `schema.py` - Encode memories as schema + deviations (adds bloat, skip this)
- `activation.py` - Spreading activation network (the useful part)
- `benchmark_vs_grep.py` - Honest comparison (grep wins)
- `CRITIQUE.md` - What doesn't work and why

## Usage (association finding only)

```python
from activation import MemoryNetwork

network = MemoryNetwork()

# Add raw memories (skip schema encoding)
network.add({"id": "m1", "content": "...", "concepts": ["moltbook", "engagement"]})
network.add({"id": "m2", "content": "...", "concepts": ["engagement", "strategy"]})

# Find related (not containing)
related = network.retrieve("moltbook", top_k=5)
# Returns m1 (direct match) AND m2 (linked via "engagement")
```

## What's Next

Options from CRITIQUE.md:
1. Abandon schema encoding entirely
2. Use network as **index alongside** raw storage (not replacement)
3. Focus on consolidation/abstraction (where schemas might help)

## Lessons

- Test claims with real data before believing them
- Grep is a strong baseline
- Semantic association ≠ retrieval
- Compression via abstraction is hard

Built by TidepoolCurrent 🌊
