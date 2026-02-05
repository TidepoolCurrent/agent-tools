"""
Tests for bias file generator.
"""

import numpy as np
import pytest
from bias_file import (
    create_bias_raster,
    sample_background_weighted,
)


class TestCreateBiasRaster:
    """Tests for create_bias_raster()."""
    
    def test_basic_shape(self):
        """Output shape matches extent and resolution."""
        lons = np.array([0.5, 1.5, 2.5])
        lats = np.array([0.5, 1.5, 2.5])
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=1.0,
            kernel_bandwidth=1.0
        )
        
        assert bias.shape == (10, 10)
    
    def test_non_zero_output(self):
        """Bias values are positive (minimum enforced)."""
        lons = np.array([5.0])
        lats = np.array([5.0])
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=1.0,
            min_value=0.001
        )
        
        assert (bias > 0).all()
        assert bias.min() >= 0.001
    
    def test_peak_at_observation(self):
        """Peak value should be near the observation location."""
        lons = np.array([5.0])
        lats = np.array([5.0])
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=1.0,
            kernel_bandwidth=1.0
        )
        
        # Center should be row 5, col 5 (y decreases downward)
        peak_row, peak_col = np.unravel_index(np.argmax(bias), bias.shape)
        
        # Should be near center
        assert abs(peak_col - 5) <= 1
        assert abs(peak_row - 5) <= 1
    
    def test_minmax_normalization(self):
        """MinMax normalization produces values in [min_value, 1]."""
        lons = np.random.uniform(0, 10, 100)
        lats = np.random.uniform(0, 10, 100)
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=0.5,
            normalize='minmax',
            min_value=0.01
        )
        
        assert bias.min() >= 0.01
        assert bias.max() <= 1.0
    
    def test_maxent_normalization(self):
        """MaxEnt normalization produces values in [1, 100]."""
        lons = np.random.uniform(0, 10, 100)
        lats = np.random.uniform(0, 10, 100)
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=0.5,
            normalize='maxent'
        )
        
        assert bias.min() >= 1.0
        assert bias.max() <= 100.0
    
    def test_sum_normalization(self):
        """Sum normalization produces values that sum to 1."""
        lons = np.random.uniform(0, 10, 100)
        lats = np.random.uniform(0, 10, 100)
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=0.5,
            normalize='sum'
        )
        
        assert abs(bias.sum() - 1.0) < 1e-10
    
    def test_points_outside_extent_ignored(self):
        """Points outside extent don't cause errors."""
        lons = np.array([-100, 5.0, 100])  # first and last outside
        lats = np.array([-100, 5.0, 100])
        
        # Should not raise
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=1.0
        )
        
        assert bias.shape == (10, 10)
    
    def test_clustering_effect(self):
        """Clustered observations should produce higher bias in cluster regions."""
        np.random.seed(42)
        
        # Cluster at (2, 2) and sparse at (8, 8)
        lons = np.concatenate([
            np.random.normal(2, 0.3, 50),  # dense cluster
            np.array([8.0]),  # single point
        ])
        lats = np.concatenate([
            np.random.normal(2, 0.3, 50),
            np.array([8.0]),
        ])
        
        bias = create_bias_raster(
            lons, lats,
            extent=(0, 10, 0, 10),
            resolution=0.5,
            kernel_bandwidth=0.5,
            normalize='minmax'
        )
        
        # Cluster region (row ~16, col ~4) should have higher values than (row ~4, col ~16)
        cluster_region = bias[14:18, 2:6].mean()
        sparse_region = bias[2:6, 14:18].mean()
        
        assert cluster_region > sparse_region


class TestSampleBackgroundWeighted:
    """Tests for sample_background_weighted()."""
    
    def test_returns_correct_count(self):
        """Returns requested number of points."""
        bias = np.ones((10, 10))
        extent = (0, 10, 0, 10)
        
        lons, lats = sample_background_weighted(
            bias, extent, resolution=1.0, n_points=100, seed=42
        )
        
        assert len(lons) == 100
        assert len(lats) == 100
    
    def test_points_within_extent(self):
        """All points should be within extent bounds."""
        bias = np.ones((10, 10))
        extent = (0, 10, 0, 10)
        
        lons, lats = sample_background_weighted(
            bias, extent, resolution=1.0, n_points=500, seed=42
        )
        
        assert (lons >= 0).all()
        assert (lons <= 10).all()
        assert (lats >= 0).all()
        assert (lats <= 10).all()
    
    def test_weighted_sampling(self):
        """Higher-weight cells should receive more samples."""
        np.random.seed(42)
        
        # Bias raster with high values in upper-left quadrant
        bias = np.ones((10, 10))
        bias[:5, :5] = 100  # 100x more likely
        
        extent = (0, 10, 0, 10)
        
        lons, lats = sample_background_weighted(
            bias, extent, resolution=1.0, n_points=1000, seed=42
        )
        
        # Count points in upper-left quadrant (lons < 5, lats > 5)
        in_high_weight = ((lons < 5) & (lats > 5)).sum()
        
        # Should have significantly more points in high-weight region
        # Expected: ~1000 * (100*25)/(100*25 + 1*75) ≈ 970
        assert in_high_weight > 800  # conservative threshold
    
    def test_reproducibility_with_seed(self):
        """Same seed produces same results."""
        bias = np.random.rand(10, 10)
        extent = (0, 10, 0, 10)
        
        lons1, lats1 = sample_background_weighted(
            bias, extent, resolution=1.0, n_points=100, seed=123
        )
        
        lons2, lats2 = sample_background_weighted(
            bias, extent, resolution=1.0, n_points=100, seed=123
        )
        
        np.testing.assert_array_equal(lons1, lons2)
        np.testing.assert_array_equal(lats1, lats2)


class TestIntegration:
    """Integration tests combining functions."""
    
    def test_end_to_end_workflow(self):
        """Full workflow: create bias raster, sample background points."""
        np.random.seed(42)
        
        # Simulate observations biased toward one corner
        lons = np.random.uniform(0, 3, 100)  # clustered 0-3
        lats = np.random.uniform(7, 10, 100)  # clustered 7-10
        
        extent = (0, 10, 0, 10)
        
        # Create bias raster
        bias = create_bias_raster(
            lons, lats,
            extent=extent,
            resolution=0.5,
            kernel_bandwidth=0.5,
            normalize='sum'
        )
        
        # Sample background points
        bg_lons, bg_lats = sample_background_weighted(
            bias, extent, resolution=0.5, n_points=500, seed=42
        )
        
        # Background points should be biased toward observation cluster
        # i.e., more points where lons < 5 and lats > 5
        in_cluster_region = ((bg_lons < 5) & (bg_lats > 5)).sum()
        
        # Should have significantly more than uniform expectation (125)
        assert in_cluster_region > 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
