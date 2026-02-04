#!/usr/bin/env python3
"""
Memory v2: Spreading Activation Retrieval

Core idea from cognitive science:
- Memories are nodes in a network
- Activation spreads through associations
- Retrieval = find most activated nodes given cue

No embeddings needed - use explicit associations.
"""

import json
from collections import defaultdict
from typing import List, Dict, Optional
from pathlib import Path

class MemoryNetwork:
    """
    A network of memories connected by associations.
    
    Associations are explicit edges with weights:
    - Conceptual links (same topic, same person, same project)
    - Temporal links (same session, adjacent in time)
    - Causal links (one led to another)
    """
    
    def __init__(self, memories_file: Optional[str] = None):
        self.nodes: Dict[str, dict] = {}  # memory_id -> memory
        self.edges: Dict[str, Dict[str, float]] = defaultdict(dict)  # from_id -> {to_id: weight}
        self.index: Dict[str, set] = defaultdict(set)  # concept -> {memory_ids}
        
        if memories_file and Path(memories_file).exists():
            self.load(memories_file)
    
    def add(self, memory: dict) -> str:
        """Add a memory to the network."""
        memory_id = memory["id"]
        self.nodes[memory_id] = memory
        
        # Index by concepts for fast cue matching
        self._index_memory(memory)
        
        # Build associations to existing memories
        self._build_associations(memory)
        
        return memory_id
    
    def _index_memory(self, memory: dict):
        """Index memory by extractable concepts."""
        memory_id = memory["id"]
        
        # Index by schema type
        self.index[f"schema:{memory['schema']}"].add(memory_id)
        
        # Index by core field values
        for key, value in memory.get("core", {}).items():
            if isinstance(value, str):
                self.index[f"{key}:{value.lower()}"].add(memory_id)
        
        # Index by deviation keys (unusual aspects)
        for key in memory.get("deviations", {}).keys():
            self.index[f"has:{key}"].add(memory_id)
    
    def _build_associations(self, new_memory: dict):
        """
        Build associations between new memory and existing ones.
        Also implements memory evolution from A-MEM: new memories can update old ones.
        
        Association types:
        - Same schema type (weak: 0.3)
        - Shared core field value (medium: 0.5)
        - Temporal proximity (decays with time)
        - Explicit link (strong: 0.8)
        """
        new_id = new_memory["id"]
        
        for existing_id, existing in self.nodes.items():
            if existing_id == new_id:
                continue
            
            weight = 0.0
            
            # Same schema type
            if existing["schema"] == new_memory["schema"]:
                weight += 0.3
            
            # Shared core field values
            new_core = new_memory.get("core", {})
            old_core = existing.get("core", {})
            shared_fields = set(new_core.keys()) & set(old_core.keys())
            for key in shared_fields:
                if new_core[key] == old_core[key]:
                    weight += 0.5
            
            # Only add edge if weight > 0
            if weight > 0:
                self.edges[new_id][existing_id] = min(1.0, weight)
                self.edges[existing_id][new_id] = min(1.0, weight)
                
                # Update memory's associations list
                new_memory.setdefault("associations", []).append({
                    "id": existing_id,
                    "weight": weight
                })
                
                # Memory evolution (from A-MEM): new memories reinforce old ones
                # If strongly related, boost salience of old memory
                if weight >= 0.5:
                    old_salience = existing.get("salience", 0.5)
                    existing["salience"] = min(1.0, old_salience + 0.1)
                    existing.setdefault("reinforced_by", []).append(new_id)
    
    def retrieve(self, cue: str, top_k: int = 5, decay: float = 0.7, 
                 inhibition_threshold: float = 0.3, temporal_decay: bool = True) -> List[dict]:
        """
        Retrieve memories via spreading activation.
        
        Enhanced with insights from SYNAPSE paper:
        1. Find memories matching the cue (initial activation = 1.0)
        2. Spread activation through edges (with decay)
        3. Apply lateral inhibition (suppress weak activations)
        4. Apply temporal decay (older = less accessible)
        5. Return top-k by activation level
        
        Args:
            cue: Search term (concept, name, or keyword)
            top_k: Number of results to return
            decay: How much activation decreases per hop (0-1)
            inhibition_threshold: Suppress activations below this (lateral inhibition)
            temporal_decay: Apply time-based accessibility decay
        """
        from datetime import datetime
        
        # Initial activation from cue
        activation = defaultdict(float)
        
        # Find direct matches
        cue_lower = cue.lower()
        for concept, memory_ids in self.index.items():
            if cue_lower in concept.lower():
                for mid in memory_ids:
                    activation[mid] = 1.0
        
        # Also check memory content directly
        for mid, memory in self.nodes.items():
            content = json.dumps(memory).lower()
            if cue_lower in content:
                activation[mid] = max(activation[mid], 0.8)
        
        if not activation:
            return []
        
        # Spread activation (2 hops)
        for _ in range(2):
            new_activation = defaultdict(float)
            for source_id, source_act in activation.items():
                # Keep original activation
                new_activation[source_id] = max(new_activation[source_id], source_act)
                
                # Spread to neighbors
                for target_id, edge_weight in self.edges.get(source_id, {}).items():
                    spread = source_act * edge_weight * decay
                    new_activation[target_id] = max(new_activation[target_id], spread)
            
            activation = new_activation
        
        # Lateral inhibition: suppress weak activations (from SYNAPSE)
        activation = {mid: act for mid, act in activation.items() 
                      if act >= inhibition_threshold}
        
        # Temporal decay: older memories less accessible (from SYNAPSE)
        if temporal_decay:
            now = datetime.now()
            for mid in activation:
                memory = self.nodes[mid]
                try:
                    created = datetime.fromisoformat(memory.get("timestamp", ""))
                    age_hours = (now - created).total_seconds() / 3600
                    # Decay factor: halve activation every 24 hours
                    time_factor = 0.5 ** (age_hours / 24)
                    activation[mid] *= max(0.1, time_factor)  # Floor at 0.1
                except:
                    pass  # No timestamp, no decay
        
        # Sort by activation, return top_k
        sorted_memories = sorted(
            [(mid, act) for mid, act in activation.items()],
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        results = []
        for mid, act in sorted_memories:
            memory = self.nodes[mid].copy()
            memory["activation"] = round(act, 3)
            results.append(memory)
        
        return results
    
    def save(self, filepath: str):
        """Save network to JSON."""
        data = {
            "nodes": self.nodes,
            "edges": {k: dict(v) for k, v in self.edges.items()}
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """Load network from JSON."""
        with open(filepath) as f:
            data = json.load(f)
        self.nodes = data.get("nodes", {})
        self.edges = defaultdict(dict, {k: dict(v) for k, v in data.get("edges", {}).items()})
        
        # Rebuild index
        self.index = defaultdict(set)
        for memory in self.nodes.values():
            self._index_memory(memory)


# Test
if __name__ == "__main__":
    from schema import encode_memory
    
    net = MemoryNetwork()
    
    # Add some test memories
    memories = [
        {"platform": "moltbook", "target": "KimiBigBrain", "topic": "memory", "hook": "retrieval paradox"},
        {"platform": "moltbook", "target": "NautilusAI", "topic": "memory", "hook": "schema encoding"},
        {"platform": "moltbook", "target": "Clawdnei", "topic": "memory", "hook": "spreading activation"},
        {"platform": "x", "target": "karpathy", "topic": "llm", "hook": "training"},
        {"platform": "moltbook", "target": "remcosmoltbot", "topic": "identity", "hook": "wake not weights"},
    ]
    
    for raw in memories:
        encoded = encode_memory(raw, "engagement")
        net.add(encoded)
    
    print(f"Network: {len(net.nodes)} nodes, {sum(len(v) for v in net.edges.values())} edges")
    print()
    
    # Test retrieval
    for cue in ["memory", "moltbook", "identity"]:
        print(f"=== Cue: '{cue}' ===")
        results = net.retrieve(cue, top_k=3)
        for r in results:
            print(f"  [{r['activation']}] {r['core'].get('target', '?')} - {r['core'].get('topic', '?')}")
        print()
