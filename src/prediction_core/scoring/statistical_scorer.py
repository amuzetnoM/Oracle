"""
Statistical Scorer - Frequency-based scoring using empirical probabilities.

This scorer estimates S(x | c) using historical frequencies:
    S(x | c) = P(x | c) ≈ count(x, c) / count(c)

Uses context quantization to group similar contexts together.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from collections import defaultdict
from .base_scorer import BaseScorer


class StatisticalScorer(BaseScorer):
    """
    Frequency-based scorer using empirical probabilities.
    
    This scorer discretizes the context space and maintains frequency counts
    of outcomes for each discretized context. It estimates:
        P(x | c) = count(x, c) / count(c)
    
    Uses Laplace smoothing to handle unseen contexts.
    """
    
    def __init__(
        self,
        name: str = "statistical_scorer",
        context_bins: int = 10,
        smoothing_alpha: float = 1.0,
        distance_metric: str = "euclidean"
    ):
        """
        Initialize statistical scorer.
        
        Args:
            name: Scorer name
            context_bins: Number of bins per context dimension
            smoothing_alpha: Laplace smoothing parameter
            distance_metric: Distance metric for context similarity
        """
        super().__init__(name)
        self.context_bins = context_bins
        self.smoothing_alpha = smoothing_alpha
        self.distance_metric = distance_metric
        
        # Storage for frequencies
        # Key: quantized context tuple, Value: dict of {candidate: count}
        self.frequencies = defaultdict(lambda: defaultdict(int))
        self.context_counts = defaultdict(int)
        
        # Context statistics for quantization
        self.context_min = None
        self.context_max = None
        self.context_dim = None
        
        # Total observations
        self.total_observations = 0
        
        # Candidate set
        self.candidates = None
        self.num_candidates = 0
    
    def _quantize_context(self, context: np.ndarray) -> Tuple[int, ...]:
        """
        Quantize continuous context into discrete bins.
        
        Args:
            context: Context vector
            
        Returns:
            Tuple of bin indices
        """
        if self.context_min is None or self.context_max is None:
            # First observation - no quantization yet
            return tuple([0] * len(context))
        
        # Normalize to [0, 1]
        normalized = (context - self.context_min) / (self.context_max - self.context_min + 1e-10)
        normalized = np.clip(normalized, 0, 1)
        
        # Discretize into bins
        bin_indices = (normalized * (self.context_bins - 1)).astype(int)
        
        return tuple(bin_indices)
    
    def _update_context_stats(self, context: np.ndarray):
        """Update context statistics for quantization."""
        if self.context_min is None:
            self.context_min = context.copy()
            self.context_max = context.copy()
            self.context_dim = len(context)
        else:
            self.context_min = np.minimum(self.context_min, context)
            self.context_max = np.maximum(self.context_max, context)
    
    def train(self, training_data: List[Dict[str, Any]]):
        """
        Train scorer on historical data.
        
        Args:
            training_data: List of examples with 'context' and 'outcome'
        """
        if not training_data:
            raise ValueError("Training data cannot be empty")
        
        # Reset state
        self.frequencies.clear()
        self.context_counts.clear()
        self.total_observations = 0
        
        # First pass: collect context statistics
        contexts = [example['context'] for example in training_data]
        contexts_array = np.array(contexts)
        self.context_min = np.min(contexts_array, axis=0)
        self.context_max = np.max(contexts_array, axis=0)
        self.context_dim = contexts_array.shape[1]
        
        # Collect all unique candidates
        all_candidates = set(example['outcome'] for example in training_data)
        self.candidates = sorted(all_candidates, key=str)
        self.num_candidates = len(self.candidates)
        
        # Second pass: build frequency table
        for example in training_data:
            context = example['context']
            outcome = example['outcome']
            
            # Quantize context
            quantized = self._quantize_context(context)
            
            # Update counts
            self.frequencies[quantized][outcome] += 1
            self.context_counts[quantized] += 1
            self.total_observations += 1
        
        self.is_trained = True
        
        # Store metadata
        self.metadata = {
            'num_examples': len(training_data),
            'num_unique_contexts': len(self.frequencies),
            'num_candidates': self.num_candidates,
            'context_dim': self.context_dim
        }
    
    def update(self, context: np.ndarray, outcome: Any):
        """
        Online update with new observation.
        
        Args:
            context: Context vector
            outcome: Observed outcome
        """
        self.validate_context(context)
        
        # Update context statistics
        self._update_context_stats(context)
        
        # Quantize and update frequencies
        quantized = self._quantize_context(context)
        self.frequencies[quantized][outcome] += 1
        self.context_counts[quantized] += 1
        self.total_observations += 1
        
        # Update candidates if new outcome seen
        if self.candidates is not None and outcome not in self.candidates:
            self.candidates = sorted(self.candidates + [outcome], key=str)
            self.num_candidates = len(self.candidates)
    
    def score(self, candidate: Any, context: np.ndarray) -> float:
        """
        Compute score S(x | c) for a candidate.
        
        Uses Laplace smoothing:
            S(x | c) = (count(x, c) + α) / (count(c) + α * |C|)
        
        Args:
            candidate: Candidate to score
            context: Context vector
            
        Returns:
            Score (estimated probability)
        """
        if not self.is_trained:
            # Uniform prior if not trained
            return 1.0 / max(1, self.num_candidates)
        
        self.validate_context(context)
        
        # Quantize context
        quantized = self._quantize_context(context)
        
        # Get counts
        candidate_count = self.frequencies[quantized].get(candidate, 0)
        total_count = self.context_counts[quantized]
        
        # Laplace smoothing
        score = (candidate_count + self.smoothing_alpha) / \
                (total_count + self.smoothing_alpha * self.num_candidates)
        
        return score
    
    def score_all(self, candidates: List[Any], context: np.ndarray) -> np.ndarray:
        """
        Compute scores for all candidates.
        
        Args:
            candidates: List of candidates
            context: Context vector
            
        Returns:
            Array of scores
        """
        scores = np.array([self.score(c, context) for c in candidates])
        return scores
    
    def get_context_distribution(self, context: np.ndarray) -> Dict[Any, float]:
        """
        Get full distribution P(x | c) for all candidates.
        
        Args:
            context: Context vector
            
        Returns:
            Dictionary mapping candidates to probabilities
        """
        if not self.is_trained:
            return {}
        
        quantized = self._quantize_context(context)
        total_count = self.context_counts[quantized]
        
        distribution = {}
        for candidate in self.candidates:
            candidate_count = self.frequencies[quantized].get(candidate, 0)
            prob = (candidate_count + self.smoothing_alpha) / \
                   (total_count + self.smoothing_alpha * self.num_candidates)
            distribution[candidate] = prob
        
        return distribution
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        base_dict = super().to_dict()
        
        # Convert defaultdict to regular dict for serialization
        frequencies_dict = {
            str(k): dict(v) for k, v in self.frequencies.items()
        }
        context_counts_dict = {
            str(k): v for k, v in self.context_counts.items()
        }
        
        base_dict.update({
            'context_bins': self.context_bins,
            'smoothing_alpha': self.smoothing_alpha,
            'distance_metric': self.distance_metric,
            'frequencies': frequencies_dict,
            'context_counts': context_counts_dict,
            'context_min': self.context_min.tolist() if self.context_min is not None else None,
            'context_max': self.context_max.tolist() if self.context_max is not None else None,
            'context_dim': self.context_dim,
            'total_observations': self.total_observations,
            'candidates': [str(c) for c in self.candidates] if self.candidates else None,
            'num_candidates': self.num_candidates
        })
        
        return base_dict
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'StatisticalScorer':
        """Load from dictionary."""
        scorer = cls(
            name=config['name'],
            context_bins=config['context_bins'],
            smoothing_alpha=config['smoothing_alpha'],
            distance_metric=config['distance_metric']
        )
        
        scorer.is_trained = config['is_trained']
        scorer.metadata = config['metadata']
        
        # Restore frequencies
        for k_str, v_dict in config['frequencies'].items():
            k = eval(k_str)  # Convert string back to tuple
            scorer.frequencies[k] = defaultdict(int, v_dict)
        
        # Restore context counts
        for k_str, v in config['context_counts'].items():
            k = eval(k_str)
            scorer.context_counts[k] = v
        
        # Restore other attributes
        if config['context_min'] is not None:
            scorer.context_min = np.array(config['context_min'])
            scorer.context_max = np.array(config['context_max'])
        scorer.context_dim = config['context_dim']
        scorer.total_observations = config['total_observations']
        scorer.num_candidates = config['num_candidates']
        
        return scorer
