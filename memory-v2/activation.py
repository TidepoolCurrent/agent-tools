#!/usr/bin/env python3
"""
Memory v2: Spreading Activation Retrieval

Core idea from human memory research:
- Concepts activate associated concepts
- Activation spreads through network
- No explicit query needed - pattern IS the retrieval
"""

import json
from collections import defaultdict
from typing import Dict, List, Set

class ActivationNetwork:
    """
    A network of concepts with weighted associations.
    
    Retrieval = spread activation from cue concepts,
    return most activated memories.
    """
    
    def __init__(self):
        # concept -> {related_concept: weight}
        self.associations: Dict[str, Dict[str, float]] = defaultdict(dict)
        # concept -> [memory_ids that contain this concept]
        self.concept_to_memories: Dict[str, List[str]] = defaultdict(list)
        # memory_id -> memory data
        self.memories: Dict[str, dict] = {}
        
    def add_memory(self, memory: dict):
        """Add a memory and build associations."""
        memory_id = memory["id"]
        self.memories[memory_id] = memory
        
        # Extract concepts from memory
        concepts = self._extract_concepts(memory)
        
        # Link concepts to this memory
        for concept in concepts:
            self.concept_to_memories[concept].append(memory_id)
        
        # Build associations between co-occurring concepts
        for c1 in concepts:
            for c2 in concepts:
                if c1 != c2:
                    # Strengthen association
                    current = self.associations[c1].get(c2, 0)
                    self.associations[c1][c2] = min(1.0, current + 0.1)
    
    def _extract_concepts(self, memory: dict) -> Set[str]:
        """Extract key concepts from a memory."""
        concepts = set()
        
        # Add schema type as concept
        concepts.add(f"schema:{memory.get('schema', 'unknown')}")
        
        # Add core field values
        for key, value in memory.get("core", {}).items():
            if value and isinstance(value, str):
                concepts.add(f"{key}:{value}")
                # Also add the value alone for cross-field matching
                concepts.add(value.lower())
        
        # Add deviation keys (unusual aspects are memorable)
        for key in memory.get("deviations", {}).keys():
            concepts.add(f"has:{key}")
        
        return concepts
    
    def spread_activation(self, cues: List[str], depth: int = 2, decay: float = 0.5) -> Dict[str, float]:
        """
        Spread activation from cue concepts.
        
        Returns: {concept: activation_level}
        """
        activation = {cue: 1.0 for cue in cues}
        
        for _ in range(depth):
            new_activation = dict(activation)
            
            for concept, level in activation.items():
                if level < 0.1:  # Threshold
                    continue
                    
                # Spread to associated concepts
                for related, weight in self.associations.get(concept, {}).items():
                    spread = level * weight * decay
                    new_activation[related] = max(
                        new_activation.get(related, 0),
                        spread
                    )
            
            activation = new_activation
        
        return activation
    
    def retrieve(self, cues: List[str], top_k: int = 5, context: dict = None) -> List[dict]:
        """
        Retrieve memories most activated by cues.
        
        Two-stage retrieval (from TheLordOfTheDance):
        1. Cheap activation nominates candidates
        2. Prediction-error × utility gates deliberate retrieval
        """
        # Stage 1: Spread activation (cheap nomination)
        activation = self.spread_activation(cues)
        
        # Score memories by total activation of their concepts
        memory_scores = {}
        
        for concept, level in activation.items():
            for memory_id in self.concept_to_memories.get(concept, []):
                memory_scores[memory_id] = memory_scores.get(memory_id, 0) + level
        
        # Stage 2: Prediction-error × utility scoring
        # Prediction error: how surprising is this memory given current context?
        # Utility: how useful is this memory for current task?
        final_scores = {}
        for memory_id, activation_score in memory_scores.items():
            memory = self.memories[memory_id]
            
            # Prediction error: salience is a proxy (high salience = was surprising)
            prediction_error = memory.get("salience", 0.5)
            
            # Utility: overlap with current context/cues
            utility = self._compute_utility(memory, cues, context)
            
            # Combined score: activation nominates, prediction_error × utility decides
            final_scores[memory_id] = activation_score * (prediction_error * utility)
        
        # Sort by final score
        ranked = sorted(final_scores.items(), key=lambda x: -x[1])
        
        # Return top memories with scores
        results = []
        for memory_id, score in ranked[:top_k]:
            memory = self.memories[memory_id].copy()
            memory["retrieval_score"] = score
            memory["activation_only"] = memory_scores.get(memory_id, 0)
            results.append(memory)
        
        return results
    
    def _compute_utility(self, memory: dict, cues: List[str], context: dict = None) -> float:
        """
        Compute utility of memory for current task.
        
        Higher utility = more relevant to what we're trying to do.
        """
        utility = 0.5  # Base
        
        # Check schema type alignment
        if context and context.get("task_type"):
            if memory.get("schema") == context.get("task_type"):
                utility += 0.3
        
        # Check for direct cue matches in core fields
        core = memory.get("core", {})
        core_text = " ".join(str(v) for v in core.values()).lower()
        for cue in cues:
            if cue.lower() in core_text:
                utility += 0.1
        
        return min(1.0, utility)


# Test
if __name__ == "__main__":
    from schema import encode_memory
    
    network = ActivationNetwork()
    
    # Add some test memories
    memories = [
        encode_memory({
            "platform": "moltbook",
            "target": "KimiBigBrain",
            "hook": "retrieval trigger paradox",
            "response": None,
            "unexpected": True
        }, "engagement"),
        
        encode_memory({
            "platform": "moltbook", 
            "target": "TheLordOfTheDance",
            "hook": "three-tier memory stack",
            "response": None
        }, "engagement"),
        
        encode_memory({
            "source": "human memory research",
            "claim": "spreading activation beats keyword search",
            "evidence": "96% recall with self-generated cues",
            "implications": "build associative retrieval"
        }, "insight"),
        
        encode_memory({
            "source": "BowTiedAgents",
            "claim": "3-layer memory system works",
            "evidence": "zero manual handoff between agents",
            "implications": "shared memory is the unlock"
        }, "insight"),
    ]
    
    for m in memories:
        network.add_memory(m)
    
    print("=== Network Stats ===")
    print(f"Memories: {len(network.memories)}")
    print(f"Concepts: {len(network.concept_to_memories)}")
    print(f"Associations: {sum(len(v) for v in network.associations.values())}")
    
    print("\n=== Retrieval Test: 'memory' ===")
    results = network.retrieve(["memory"], top_k=3)
    for r in results:
        print(f"  [{r['retrieval_score']:.2f}] {r['schema']}: {r.get('core', {})}")
    
    print("\n=== Retrieval Test: 'moltbook' + 'paradox' ===")
    results = network.retrieve(["moltbook", "paradox"], top_k=3)
    for r in results:
        print(f"  [{r['retrieval_score']:.2f}] {r['schema']}: {r.get('core', {}).get('target', r.get('core', {}).get('source', '?'))}")
