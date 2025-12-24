"""
Base Scorer Interface - Abstract base class for all scoring functions.

All scoring functions must implement the score() method which evaluates
S(x | c) for a candidate x given context c.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np


class BaseScorer(ABC):
    """
    Abstract base class for all scoring functions.
    
    A scorer evaluates S(x | c) - the score of candidate x given context c.
    Higher scores indicate higher preference for that candidate.
    """
    
    def __init__(self, name: str = "base_scorer"):
        """
        Initialize the scorer.
        
        Args:
            name: Name of the scorer
        """
        self.name = name
        self.is_trained = False
        self.metadata = {}
    
    @abstractmethod
    def score(self, candidate: Any, context: np.ndarray) -> float:
        """
        Compute the score S(x | c) for a candidate given context.
        
        Args:
            candidate: The candidate to score
            context: Context vector (features)
            
        Returns:
            Score value (higher is better)
        """
        pass
    
    @abstractmethod
    def score_all(self, candidates: List[Any], context: np.ndarray) -> np.ndarray:
        """
        Compute scores for all candidates given context.
        
        Args:
            candidates: List of candidates to score
            context: Context vector (features)
            
        Returns:
            Array of scores, one per candidate
        """
        pass
    
    @abstractmethod
    def train(self, training_data: List[Dict[str, Any]]):
        """
        Train the scorer on historical data.
        
        Args:
            training_data: List of training examples, each with:
                - 'context': Context vector
                - 'outcome': Actual outcome that occurred
                - 'timestamp': Optional timestamp
        """
        pass
    
    def update(self, context: np.ndarray, outcome: Any):
        """
        Update the scorer with a single new observation.
        
        Args:
            context: Context vector
            outcome: Observed outcome
        """
        # Default: retrain on new data
        # Subclasses can implement online learning
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize scorer to dictionary.
        
        Returns:
            Dictionary containing scorer state
        """
        return {
            'name': self.name,
            'is_trained': self.is_trained,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BaseScorer':
        """
        Load scorer from dictionary.
        
        Args:
            config: Dictionary containing scorer state
            
        Returns:
            Reconstructed scorer instance
        """
        raise NotImplementedError("Subclasses must implement from_dict")
    
    def validate_context(self, context: np.ndarray):
        """
        Validate that context has correct shape/format.
        
        Args:
            context: Context vector to validate
            
        Raises:
            ValueError: If context is invalid
        """
        if not isinstance(context, np.ndarray):
            raise ValueError(f"Context must be numpy array, got {type(context)}")
        
        if len(context.shape) != 1:
            raise ValueError(f"Context must be 1D array, got shape {context.shape}")
