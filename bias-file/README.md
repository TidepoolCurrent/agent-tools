# Bias File Generator for SDM

Creates sampling effort bias files from iNaturalist (or other) observation data.

## Why Bias Files?

Presence-only SDMs (like MaxEnt) need background points. If sampled uniformly, 
but presence data is biased toward roads/cities/trails, the model will overpredict 
suitability in high-effort areas.

**Solution:** Sample background points proportionally to observation effort.

## Usage

```python
from bias_file import create_bias_raster

# From iNaturalist observations (any taxa - captures general effort)
bias = create_bias_raster(
    observations_csv='inaturalist_obs.csv',  # lat, lon columns
    extent=(-130, -110, 30, 50),  # xmin, xmax, ymin, ymax
    resolution=0.1,  # degrees
    kernel_bandwidth=1.0,  # smoothing in degrees
    output_path='effort_bias.tif'
)

# Use with elapid or maxent
import elapid
background = elapid.pseudoabsence_from_raster(bias, count=10000, weighted=True)
```

## Method

1. Load observation coordinates
2. Create grid over extent
3. Apply kernel density estimation (Gaussian kernel)
4. Normalize to 0-1 range (or 1-100 for MaxEnt GUI)
5. Export as GeoTIFF

## References

- Kramer-Schadt et al. 2013. "Effects of Sampling Bias and Model Complexity"
- Fourcade et al. 2014. "Mapping Species Distributions with MAXENT Using Geographically Biased Sample"
- Phillips et al. 2009. "Sample selection bias and presence-only distribution models"
