"""
Candidate Space - Defines the set of all possible predictions.

The candidate space C represents all possible outcomes the system can predict.
For financial predictions, this typically includes:
- Direction: UP, DOWN, FLAT
- Magnitude: Discretized price change bins
"""

from typing import List, Dict, Any, Union, Optional
from enum import Enum
import numpy as np


class Direction(Enum):
    """Price direction candidates."""
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


class CandidateSpace:
    """
    Defines and manages the candidate space C for predictions.
    
    The candidate space can be:
    1. Discrete directions (UP/DOWN/FLAT)
    2. Continuous bins (discretized price changes)
    3. Hybrid (direction + magnitude)
    """
    
    def __init__(
        self,
        candidate_type: str = "direction",
        num_bins: Optional[int] = None,
        bin_edges: Optional[np.ndarray] = None,
        custom_candidates: Optional[List[Any]] = None
    ):
        """
        Initialize candidate space.
        
        Args:
            candidate_type: Type of candidates ("direction", "bins", "hybrid", "custom")
            num_bins: Number of bins for continuous discretization
            bin_edges: Custom bin edges for continuous values
            custom_candidates: Custom candidate set
        """
        self.candidate_type = candidate_type
        self.num_bins = num_bins
        self.bin_edges = bin_edges
        self.custom_candidates = custom_candidates
        
        # Initialize the candidate space
        self._initialize_candidates()
    
    def _initialize_candidates(self):
        """Initialize the candidate set based on type."""
        if self.candidate_type == "direction":
            self.candidates = [Direction.UP, Direction.DOWN, Direction.FLAT]
            self.num_candidates = 3
            
        elif self.candidate_type == "bins":
            if self.bin_edges is not None:
                self.candidates = list(range(len(self.bin_edges) - 1))
                self.num_candidates = len(self.candidates)
            elif self.num_bins is not None:
                # Create uniform bins between -1 and 1 (percentage changes)
                self.bin_edges = np.linspace(-1.0, 1.0, self.num_bins + 1)
                self.candidates = list(range(self.num_bins))
                self.num_candidates = self.num_bins
            else:
                raise ValueError("Must provide either bin_edges or num_bins for 'bins' type")
                
        elif self.candidate_type == "hybrid":
            # Combination of direction and magnitude bins
            directions = [Direction.UP, Direction.DOWN, Direction.FLAT]
            if self.num_bins is None:
                self.num_bins = 5  # Default magnitude bins
            
            self.candidates = [
                (direction, bin_idx) 
                for direction in directions 
                for bin_idx in range(self.num_bins)
            ]
            self.num_candidates = len(self.candidates)
            
        elif self.candidate_type == "custom":
            if self.custom_candidates is None:
                raise ValueError("Must provide custom_candidates for 'custom' type")
            self.candidates = self.custom_candidates
            self.num_candidates = len(self.candidates)
            
        else:
            raise ValueError(f"Unknown candidate_type: {self.candidate_type}")
    
    def get_candidates(self) -> List[Any]:
        """Return the list of all candidates."""
        return self.candidates
    
    def get_num_candidates(self) -> int:
        """Return the number of candidates."""
        return self.num_candidates
    
    def get_candidate_index(self, candidate: Any) -> int:
        """
        Get the index of a candidate in the candidate list.
        
        Args:
            candidate: The candidate to find
            
        Returns:
            Index of the candidate
        """
        try:
            return self.candidates.index(candidate)
        except ValueError:
            raise ValueError(f"Candidate {candidate} not in candidate space")
    
    def discretize_value(self, value: float) -> Any:
        """
        Convert a continuous value to a discrete candidate.
        
        Args:
            value: Continuous value (e.g., price change percentage)
            
        Returns:
            Corresponding candidate
        """
        if self.candidate_type == "direction":
            if value > 0.001:  # Small threshold for noise
                return Direction.UP
            elif value < -0.001:
                return Direction.DOWN
            else:
                return Direction.FLAT
                
        elif self.candidate_type == "bins":
            # Find which bin the value falls into
            bin_idx = np.digitize(value, self.bin_edges) - 1
            # Clamp to valid range
            bin_idx = max(0, min(bin_idx, self.num_bins - 1))
            return self.candidates[bin_idx]
            
        elif self.candidate_type == "hybrid":
            # Determine direction
            if value > 0.001:
                direction = Direction.UP
            elif value < -0.001:
                direction = Direction.DOWN
            else:
                direction = Direction.FLAT
            
            # Determine magnitude bin
            abs_value = abs(value)
            bin_edges = np.linspace(0, 1.0, self.num_bins + 1)
            bin_idx = np.digitize(abs_value, bin_edges) - 1
            bin_idx = max(0, min(bin_idx, self.num_bins - 1))
            
            return (direction, bin_idx)
            
        else:
            raise NotImplementedError(f"Discretization not implemented for {self.candidate_type}")
    
    def candidate_to_value(self, candidate: Any) -> float:
        """
        Convert a candidate back to a representative continuous value.
        
        Args:
            candidate: The candidate
            
        Returns:
            Representative continuous value
        """
        if self.candidate_type == "direction":
            if candidate == Direction.UP:
                return 0.01  # 1% up
            elif candidate == Direction.DOWN:
                return -0.01  # 1% down
            else:
                return 0.0  # Flat
                
        elif self.candidate_type == "bins":
            # Return bin center
            bin_idx = candidate
            return (self.bin_edges[bin_idx] + self.bin_edges[bin_idx + 1]) / 2
            
        elif self.candidate_type == "hybrid":
            direction, bin_idx = candidate
            # Get magnitude from bin
            bin_edges = np.linspace(0, 1.0, self.num_bins + 1)
            magnitude = (bin_edges[bin_idx] + bin_edges[bin_idx + 1]) / 2
            
            # Apply direction
            if direction == Direction.UP:
                return magnitude
            elif direction == Direction.DOWN:
                return -magnitude
            else:
                return 0.0
                
        else:
            raise NotImplementedError(f"Value conversion not implemented for {self.candidate_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize candidate space to dictionary."""
        return {
            'candidate_type': self.candidate_type,
            'num_bins': self.num_bins,
            'bin_edges': self.bin_edges.tolist() if self.bin_edges is not None else None,
            'num_candidates': self.num_candidates
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'CandidateSpace':
        """Load candidate space from dictionary."""
        bin_edges = config.get('bin_edges')
        if bin_edges is not None:
            bin_edges = np.array(bin_edges)
        
        return cls(
            candidate_type=config['candidate_type'],
            num_bins=config.get('num_bins'),
            bin_edges=bin_edges
        )
