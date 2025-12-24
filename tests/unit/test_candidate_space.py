"""
Unit tests for CandidateSpace.
"""

import pytest
import numpy as np
from src.prediction_core import CandidateSpace, Direction


class TestCandidateSpace:
    """Test suite for CandidateSpace."""
    
    def test_direction_candidate_space(self):
        """Test direction-based candidate space."""
        cs = CandidateSpace(candidate_type="direction")
        
        assert cs.num_candidates == 3
        assert Direction.UP in cs.candidates
        assert Direction.DOWN in cs.candidates
        assert Direction.FLAT in cs.candidates
    
    def test_bins_candidate_space(self):
        """Test bins-based candidate space."""
        cs = CandidateSpace(candidate_type="bins", num_bins=5)
        
        assert cs.num_candidates == 5
        assert len(cs.candidates) == 5
        assert cs.bin_edges is not None
    
    def test_hybrid_candidate_space(self):
        """Test hybrid candidate space."""
        cs = CandidateSpace(candidate_type="hybrid", num_bins=3)
        
        # 3 directions × 3 magnitude bins = 9 candidates
        assert cs.num_candidates == 9
        assert len(cs.candidates) == 9
    
    def test_discretize_direction(self):
        """Test discretization of continuous values to directions."""
        cs = CandidateSpace(candidate_type="direction")
        
        assert cs.discretize_value(0.05) == Direction.UP
        assert cs.discretize_value(-0.03) == Direction.DOWN
        assert cs.discretize_value(0.0005) == Direction.FLAT
    
    def test_discretize_bins(self):
        """Test discretization to bins."""
        cs = CandidateSpace(candidate_type="bins", num_bins=5)
        
        # Test various values
        candidate = cs.discretize_value(0.5)
        assert candidate in cs.candidates
        
        candidate = cs.discretize_value(-0.5)
        assert candidate in cs.candidates
    
    def test_candidate_to_value(self):
        """Test converting candidate back to value."""
        cs = CandidateSpace(candidate_type="direction")
        
        up_value = cs.candidate_to_value(Direction.UP)
        assert up_value > 0
        
        down_value = cs.candidate_to_value(Direction.DOWN)
        assert down_value < 0
        
        flat_value = cs.candidate_to_value(Direction.FLAT)
        assert flat_value == 0.0
    
    def test_candidate_index(self):
        """Test getting candidate indices."""
        cs = CandidateSpace(candidate_type="direction")
        
        idx = cs.get_candidate_index(Direction.UP)
        assert 0 <= idx < 3
        assert cs.candidates[idx] == Direction.UP
    
    def test_serialization(self):
        """Test to_dict and from_dict."""
        cs = CandidateSpace(candidate_type="bins", num_bins=5)
        
        config = cs.to_dict()
        assert config['candidate_type'] == 'bins'
        assert config['num_bins'] == 5
        
        # Reconstruct
        cs2 = CandidateSpace.from_dict(config)
        assert cs2.candidate_type == cs.candidate_type
        assert cs2.num_bins == cs.num_bins
    
    def test_invalid_candidate_type(self):
        """Test error handling for invalid candidate type."""
        with pytest.raises(ValueError):
            CandidateSpace(candidate_type="invalid")
    
    def test_custom_bin_edges(self):
        """Test custom bin edges."""
        edges = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        cs = CandidateSpace(candidate_type="bins", bin_edges=edges)
        
        assert cs.num_candidates == 4
        assert np.array_equal(cs.bin_edges, edges)
