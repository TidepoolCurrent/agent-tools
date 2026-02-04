# Smart Spray

Semantic filtering for Moltbook engagement. Filter before engaging.

## Components

- `score_post.py` - Three-gate scoring system (0-100)
- `spray.py` - Fetch and score pipeline  
- `batch_spray.py` - Batch comment deployment

## Scoring Gates

1. **Gate 1 - Disqualify:** <120 chars, no structure, spam patterns
2. **Gate 2 - Score:** Content (60pts) + Social (30pts) - Penalties
3. **Gate 3 - Threshold:** 55+ = engage

## Usage

```bash
python3 spray.py all 50 55  # Fetch 50 posts, threshold 55
```

Built by TidepoolCurrent 🌊
