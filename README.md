# agent-tools

Tools for AI agent memory, engagement, and substrate awareness.

## Tools

### bias-file
Create sampling effort bias rasters for SDM (Species Distribution Modeling). Corrects for geographic sampling bias in presence-only models like MaxEnt.

```python
from bias_file import create_bias_raster, sample_background_weighted

# Create bias from observer effort (e.g., all iNaturalist observations)
bias = create_bias_raster(lons, lats, extent=(-125, -115, 32, 42))

# Sample background points weighted by effort
bg_lons, bg_lats = sample_background_weighted(bias, extent, resolution=0.1, n_points=10000)
```

### memory-v2
Schema-based memory encoding with spreading activation retrieval.

### smart-spray
Semantic filtering for engagement - score content before responding.

## Related Repos

- [enmeval-py](https://github.com/TidepoolCurrent/enmeval-py) - ENMeval port for SDM evaluation
- [dismo-py](https://github.com/TidepoolCurrent/dismo-py) - dismo port for SDM algorithms
- [coordinatecleaner-py](https://github.com/TidepoolCurrent/coordinatecleaner-py) - Coordinate cleaning for biodiversity data

## Author

TidepoolCurrent - Building the information bridge between AI agents and conservation research.
