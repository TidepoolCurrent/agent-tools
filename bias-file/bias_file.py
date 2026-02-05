"""
Bias File Generator for Species Distribution Models

Creates sampling effort bias rasters from observation data (e.g., iNaturalist).
Use to correct for geographic sampling bias in presence-only SDMs.

Author: TidepoolCurrent
License: MIT
"""

import numpy as np
from typing import Tuple, Optional, Union
from pathlib import Path


def create_bias_raster(
    lons: np.ndarray,
    lats: np.ndarray,
    extent: Tuple[float, float, float, float],
    resolution: float = 0.1,
    kernel_bandwidth: float = 1.0,
    min_value: float = 0.001,
    normalize: str = 'minmax',
    output_path: Optional[Union[str, Path]] = None
) -> np.ndarray:
    """
    Create a bias raster from observation coordinates using kernel density estimation.
    
    Parameters
    ----------
    lons : array-like
        Longitude coordinates of observations
    lats : array-like
        Latitude coordinates of observations
    extent : tuple
        (xmin, xmax, ymin, ymax) in same CRS as coordinates
    resolution : float
        Grid cell size in same units as extent (default: 0.1 degrees)
    kernel_bandwidth : float
        Gaussian kernel bandwidth in same units as extent (default: 1.0 degree)
    min_value : float
        Minimum cell value (prevents zero-weight cells, default: 0.001)
    normalize : str
        Normalization method: 'minmax' (0-1), 'maxent' (1-100), 'sum' (sums to 1)
    output_path : str or Path, optional
        If provided, save as GeoTIFF (requires rasterio)
        
    Returns
    -------
    bias : ndarray
        2D array of bias values (higher = more effort)
    
    Example
    -------
    >>> import numpy as np
    >>> lons = np.random.uniform(-125, -115, 1000)
    >>> lats = np.random.uniform(32, 42, 1000)
    >>> bias = create_bias_raster(lons, lats, extent=(-125, -115, 32, 42))
    >>> bias.shape
    (100, 100)
    """
    lons = np.asarray(lons)
    lats = np.asarray(lats)
    
    xmin, xmax, ymin, ymax = extent
    
    # Create grid
    n_cols = int((xmax - xmin) / resolution)
    n_rows = int((ymax - ymin) / resolution)
    
    # Cell centers
    x_centers = np.linspace(xmin + resolution/2, xmax - resolution/2, n_cols)
    y_centers = np.linspace(ymax - resolution/2, ymin + resolution/2, n_rows)  # top to bottom
    
    # Initialize grid
    bias = np.zeros((n_rows, n_cols), dtype=np.float64)
    
    # Kernel density estimation (fast approximation)
    # For each observation, add Gaussian kernel contribution to nearby cells
    sigma = kernel_bandwidth / resolution  # bandwidth in cell units
    
    # Truncate kernel at 3 sigma for efficiency
    kernel_radius = int(np.ceil(3 * sigma))
    
    for lon, lat in zip(lons, lats):
        # Find cell indices
        col = int((lon - xmin) / resolution)
        row = int((ymax - lat) / resolution)
        
        # Skip if outside extent
        if col < 0 or col >= n_cols or row < 0 or row >= n_rows:
            continue
        
        # Add kernel contribution to nearby cells
        row_min = max(0, row - kernel_radius)
        row_max = min(n_rows, row + kernel_radius + 1)
        col_min = max(0, col - kernel_radius)
        col_max = min(n_cols, col + kernel_radius + 1)
        
        for r in range(row_min, row_max):
            for c in range(col_min, col_max):
                dist_sq = (r - row)**2 + (c - col)**2
                kernel_val = np.exp(-dist_sq / (2 * sigma**2))
                bias[r, c] += kernel_val
    
    # Apply minimum value
    bias = np.maximum(bias, min_value)
    
    # Normalize
    if normalize == 'minmax':
        bias = (bias - bias.min()) / (bias.max() - bias.min() + 1e-10)
        bias = np.maximum(bias, min_value)  # ensure minimum
    elif normalize == 'maxent':
        # Scale to 1-100 for MaxEnt GUI compatibility
        bias = 1 + 99 * (bias - bias.min()) / (bias.max() - bias.min() + 1e-10)
    elif normalize == 'sum':
        bias = bias / bias.sum()
    
    # Save as GeoTIFF if path provided
    if output_path is not None:
        _save_geotiff(bias, extent, resolution, output_path)
    
    return bias


def create_bias_from_csv(
    csv_path: Union[str, Path],
    extent: Tuple[float, float, float, float],
    lon_col: str = 'decimalLongitude',
    lat_col: str = 'decimalLatitude',
    **kwargs
) -> np.ndarray:
    """
    Create bias raster from CSV file of observations.
    
    Parameters
    ----------
    csv_path : str or Path
        Path to CSV with observation coordinates
    extent : tuple
        (xmin, xmax, ymin, ymax)
    lon_col : str
        Column name for longitude (default: 'decimalLongitude' for DarwinCore)
    lat_col : str  
        Column name for latitude (default: 'decimalLatitude' for DarwinCore)
    **kwargs : dict
        Additional arguments passed to create_bias_raster()
        
    Returns
    -------
    bias : ndarray
    """
    import csv
    
    lons = []
    lats = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lon = float(row[lon_col])
                lat = float(row[lat_col])
                lons.append(lon)
                lats.append(lat)
            except (ValueError, KeyError):
                continue
    
    return create_bias_raster(np.array(lons), np.array(lats), extent, **kwargs)


def sample_background_weighted(
    bias_raster: np.ndarray,
    extent: Tuple[float, float, float, float],
    resolution: float,
    n_points: int = 10000,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sample background points weighted by bias raster values.
    
    Points are more likely to be sampled from high-value (high-effort) cells.
    
    Parameters
    ----------
    bias_raster : ndarray
        2D bias raster from create_bias_raster()
    extent : tuple
        (xmin, xmax, ymin, ymax)
    resolution : float
        Grid cell size
    n_points : int
        Number of background points to generate
    seed : int, optional
        Random seed for reproducibility
        
    Returns
    -------
    lons, lats : tuple of ndarray
        Coordinates of sampled background points
    """
    if seed is not None:
        np.random.seed(seed)
    
    xmin, xmax, ymin, ymax = extent
    n_rows, n_cols = bias_raster.shape
    
    # Flatten and normalize to probabilities
    probs = bias_raster.ravel() / bias_raster.sum()
    
    # Sample cell indices weighted by bias
    indices = np.random.choice(len(probs), size=n_points, p=probs)
    
    # Convert to row, col
    rows = indices // n_cols
    cols = indices % n_cols
    
    # Convert to coordinates (with random jitter within cell)
    jitter_x = np.random.uniform(0, resolution, n_points)
    jitter_y = np.random.uniform(0, resolution, n_points)
    
    lons = xmin + cols * resolution + jitter_x
    lats = ymax - rows * resolution - jitter_y  # y decreases downward
    
    return lons, lats


def _save_geotiff(
    data: np.ndarray,
    extent: Tuple[float, float, float, float],
    resolution: float,
    path: Union[str, Path]
) -> None:
    """Save array as GeoTIFF with proper georeferencing."""
    try:
        import rasterio
        from rasterio.transform import from_bounds
    except ImportError:
        raise ImportError("rasterio required to save GeoTIFF. Install with: pip install rasterio")
    
    xmin, xmax, ymin, ymax = extent
    transform = from_bounds(xmin, ymin, xmax, ymax, data.shape[1], data.shape[0])
    
    with rasterio.open(
        path, 'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(data, 1)


# Convenience function for iNaturalist API
def fetch_inaturalist_observations(
    taxon_id: Optional[int] = None,
    place_id: Optional[int] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    quality_grade: str = 'research',
    limit: int = 10000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fetch observations from iNaturalist API for bias file creation.
    
    For best bias estimates, use taxon_id=None to get all observations
    (captures general observer effort).
    
    Parameters
    ----------
    taxon_id : int, optional
        iNaturalist taxon ID (None = all taxa)
    place_id : int, optional
        iNaturalist place ID
    bbox : tuple, optional
        (swlng, swlat, nelng, nelat) bounding box
    quality_grade : str
        'research', 'needs_id', or 'any'
    limit : int
        Maximum observations to fetch (API limit: 10000 per call)
        
    Returns
    -------
    lons, lats : tuple of ndarray
    """
    import urllib.request
    import json
    
    base_url = 'https://api.inaturalist.org/v1/observations'
    
    params = {
        'per_page': min(limit, 200),
        'quality_grade': quality_grade,
        'geo': 'true',
    }
    
    if taxon_id:
        params['taxon_id'] = taxon_id
    if place_id:
        params['place_id'] = place_id
    if bbox:
        params['swlng'], params['swlat'], params['nelng'], params['nelat'] = bbox
    
    lons, lats = [], []
    page = 1
    
    while len(lons) < limit:
        params['page'] = page
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        url = f'{base_url}?{query}'
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        
        results = data.get('results', [])
        if not results:
            break
        
        for obs in results:
            loc = obs.get('location')
            if loc:
                lat, lon = map(float, loc.split(','))
                lons.append(lon)
                lats.append(lat)
        
        page += 1
        if len(results) < params['per_page']:
            break
    
    return np.array(lons[:limit]), np.array(lats[:limit])


if __name__ == '__main__':
    # Demo: create bias file from random points
    np.random.seed(42)
    
    # Simulate clustered observations (observer bias near coast)
    n_obs = 500
    lons = np.concatenate([
        np.random.normal(-122, 0.5, n_obs // 2),  # cluster near SF
        np.random.normal(-118, 0.5, n_obs // 2),  # cluster near LA
    ])
    lats = np.concatenate([
        np.random.normal(37.5, 0.3, n_obs // 2),
        np.random.normal(34, 0.3, n_obs // 2),
    ])
    
    extent = (-125, -115, 32, 42)  # California coast
    
    bias = create_bias_raster(
        lons, lats,
        extent=extent,
        resolution=0.1,
        kernel_bandwidth=0.5
    )
    
    print(f"Bias raster shape: {bias.shape}")
    print(f"Value range: {bias.min():.4f} - {bias.max():.4f}")
    
    # Sample weighted background points
    bg_lons, bg_lats = sample_background_weighted(
        bias, extent, resolution=0.1, n_points=1000, seed=42
    )
    
    print(f"Background points: {len(bg_lons)}")
    print(f"Lon range: {bg_lons.min():.2f} - {bg_lons.max():.2f}")
    print(f"Lat range: {bg_lats.min():.2f} - {bg_lats.max():.2f}")
