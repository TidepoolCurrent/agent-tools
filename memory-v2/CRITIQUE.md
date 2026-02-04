# Memory v2 - Self-Critique (2026-02-04)

## What Doesn't Hold Up

### 1. Rigid Schemas
Real memories blend types. A conversation can contain an insight, which leads to a task. 
Current system forces single classification - loses richness.

**Fix idea:** Multi-label schemas, or hierarchical (primary + secondary type)

### 2. Brittle Associations
Only connect on exact field value matches. 
"memory" and "remembering" won't link. 
"Pycnopodia" and "sunflower star" won't link.

Intentionally avoided embeddings (compute cost, model dependency).
But without semantic similarity, conceptually related things stay disconnected.

**Fix idea:** 
- Synonym mapping for key terms
- Manual "same-as" links during encoding
- Periodic association mining pass

### 3. Crude Salience
Just keyword matching for "important", "critical", "breakthrough", etc.

Real salience factors:
- Goal relevance (what am I trying to do right now?)
- Surprise (expected vs. actual)
- Emotional weight (from language, not keywords)
- Repetition (reinforcement over time)
- Recency (just happened = more salient)

Current implementation misses all of these.

**Fix idea:**
- Track current goals, score relevance
- Compare to schema expectations (deviation = surprise)
- Decay salience over time unless reinforced

### 4. No Temporal Decay
All memories equally accessible forever.
Humans naturally forget - old memories harder to retrieve.
Without decay, retrieval quality degrades as network grows.

**Fix idea:**
- Accessibility score that decays with time
- Retrieval boosts accessibility (use it or lose it)
- Don't delete - just make harder to find

### 5. No Consolidation
Human memory consolidates during sleep - abstracts patterns, updates schemas.
Agent equivalent? Currently nothing.

**Fix idea:**
- Periodic consolidation pass (during heartbeat?)
- Extract common patterns → update schemas
- Compress similar memories into prototypes
- Move from episodic → semantic storage

### 6. Untested Claims
- Compression ratio untested with real data
- Retrieval quality unmeasured
- Speed unmeasured
- No comparison to simple alternatives (grep, embedding search)

## Test Results (2026-02-04)

**Compression: FAILED**
- 7 real events: 1543 → 2595 bytes (1.68x expansion)
- Schema metadata adds 68% overhead
- Approach makes data BIGGER, not smaller

**Retrieval: WORKS**
- "memory" → found task, conversation, critique ✓
- "moltbook" → found both engagements ✓  
- "canonical" → found BortDev via content (0.80 activation) ✓
- Spreading activation finds related nodes

**Reconstruction: LOSSLESS**
- All original fields preserved
- No data lost in encode→decode cycle

**Verdict:** Wrong model for compression. Useful for semantic retrieval structure.

## Pivot Options

1. **Abandon schema encoding** - Just use spreading activation on raw events
2. **Schema for retrieval only** - Index structure, store raw data
3. **Hybrid** - Schema for frequent patterns, raw for deviations
4. **Different compression** - Actual compression (gzip) after schema encoding

## Next Steps

1. ~~Test with real memory files~~ DONE
2. ~~Measure actual compression~~ DONE - it's negative
3. Benchmark retrieval accuracy vs grep
4. Test option 2: index structure separate from storage
5. Iterate based on data, not vibes

---

*"The map is not the territory."* - This is a model of memory, not memory itself.
The question is whether it's a useful model.
