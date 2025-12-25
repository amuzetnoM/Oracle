"""
Ensemble Scorer - Combines multiple scorers using weighted averaging.

This scorer aggregates predictions from multiple base scorers:
    S_ensemble(x | c) = Σ w_i * S_i(x | c)

Weights can be uniform or learned based on performance.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from .base_scorer import BaseScorer


class EnsembleScorer(BaseScorer):
    """
    Ensemble scorer that combines multiple base scorers.
    
    Supports multiple combination strategies:
    - Weighted average: S = Σ w_i * S_i
    - Weighted geometric mean: S = ∏ S_i^w_i
    - Maximum: S = max(S_i)
    - Voting: S = most frequent argmax
    """
    
    def __init__(
        self,
        scorers: List[BaseScorer],
        weights: Optional[List[float]] = None,
        combination: str = "weighted_average",
        name: str = "ensemble_scorer"
    ):
        """
        Initialize ensemble scorer.
        
        Args:
            scorers: List of base scorers to combine
            weights: Weight for each scorer (None = uniform)
            combination: How to combine scores ("weighted_average", "geometric_mean",
                        "max", "voting")
            name: Scorer name
        """
        super().__init__(name)
        
        if not scorers:
            raise ValueError("Must provide at least one scorer")
        
        self.scorers = scorers
        self.num_scorers = len(scorers)
        
        # Initialize weights
        if weights is None:
            self.weights = np.ones(self.num_scorers) / self.num_scorers
        else:
            if len(weights) != self.num_scorers:
                raise ValueError(f"Number of weights ({len(weights)}) must match number of scorers ({self.num_scorers})")
            self.weights = np.array(weights)
            # Normalize weights
            self.weights = self.weights / np.sum(self.weights)
        
        self.combination = combination
        
        # Ensemble is trained if all base scorers are trained
        self.is_trained = all(scorer.is_trained for scorer in self.scorers)
    
    def train(self, training_data: List[Dict[str, Any]]):
        """
        Train all base scorers.
        
        Args:
            training_data: Training examples
        """
        for scorer in self.scorers:
            if not scorer.is_trained:
                scorer.train(training_data)
        
        self.is_trained = True
        
        self.metadata = {
            'num_scorers': self.num_scorers,
            'combination': self.combination,
            'weights': self.weights.tolist()
        }
    
    def score(self, candidate: Any, context: np.ndarray) -> float:
        """
        Compute ensemble score.
        
        Args:
            candidate: Candidate to score
            context: Context vector
            
        Returns:
            Combined score
        """
        if not self.is_trained:
            return 1.0 / self.num_scorers
        
        self.validate_context(context)
        
        # Get scores from all base scorers
        scores = np.array([scorer.score(candidate, context) for scorer in self.scorers])
        
        # Combine based on strategy
        if self.combination == "weighted_average":
            return np.dot(self.weights, scores)
        
        elif self.combination == "geometric_mean":
            # Geometric mean: (∏ S_i^w_i)
            # In log space: exp(Σ w_i * log(S_i))
            log_scores = np.log(scores + 1e-10)  # Add small value to avoid log(0)
            return np.exp(np.dot(self.weights, log_scores))
        
        elif self.combination == "max":
            return np.max(scores)
        
        else:
            raise ValueError(f"Unknown combination strategy: {self.combination}")
    
    def score_all(self, candidates: List[Any], context: np.ndarray) -> np.ndarray:
        """
        Compute ensemble scores for all candidates.
        
        Args:
            candidates: List of candidates
            context: Context vector
            
        Returns:
            Array of scores
        """
        if not self.is_trained:
            return np.ones(len(candidates)) / len(candidates)
        
        self.validate_context(context)
        
        if self.combination == "voting":
            # Each scorer votes for its argmax
            votes = np.zeros(len(candidates))
            
            for i, scorer in enumerate(self.scorers):
                scorer_scores = scorer.score_all(candidates, context)
                winner_idx = np.argmax(scorer_scores)
                votes[winner_idx] += self.weights[i]
            
            return votes / np.sum(votes)
        
        else:
            # Get scores from all base scorers
            all_scores = np.array([
                scorer.score_all(candidates, context)
                for scorer in self.scorers
            ])  # Shape: (num_scorers, num_candidates)
            
            # Combine based on strategy
            if self.combination == "weighted_average":
                combined = np.dot(self.weights, all_scores)
            
            elif self.combination == "geometric_mean":
                log_scores = np.log(all_scores + 1e-10)
                combined = np.exp(np.dot(self.weights, log_scores))
            
            elif self.combination == "max":
                combined = np.max(all_scores, axis=0)
            
            else:
                raise ValueError(f"Unknown combination strategy: {self.combination}")
            
            return combined
    
    def update(self, context: np.ndarray, outcome: Any):
        """
        Update all base scorers.
        
        Args:
            context: Context vector
            outcome: Observed outcome
        """
        for scorer in self.scorers:
            scorer.update(context, outcome)
    
    def optimize_weights(
        self,
        validation_data: List[Dict[str, Any]],
        candidates: List[Any]
    ):
        """
        Optimize ensemble weights based on validation performance.
        
        Uses grid search to find weights that minimize validation error.
        
        Args:
            validation_data: Validation examples
            candidates: List of all candidates
        """
        if not validation_data:
            return
        
        best_weights = self.weights.copy()
        best_accuracy = self._compute_accuracy(validation_data, candidates)
        
        # Simple grid search over weights
        # For 2 scorers: try different weight combinations
        # For more scorers: sample random weight combinations
        
        if self.num_scorers == 2:
            # Exhaustive search for 2 scorers
            for w1 in np.linspace(0, 1, 21):
                test_weights = np.array([w1, 1 - w1])
                self.weights = test_weights
                accuracy = self._compute_accuracy(validation_data, candidates)
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_weights = test_weights.copy()
        
        else:
            # Random search for more scorers
            for _ in range(100):
                # Sample random weights from Dirichlet distribution
                test_weights = np.random.dirichlet(np.ones(self.num_scorers))
                self.weights = test_weights
                accuracy = self._compute_accuracy(validation_data, candidates)
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_weights = test_weights.copy()
        
        # Set best weights
        self.weights = best_weights
        
        self.metadata['optimized_weights'] = self.weights.tolist()
        self.metadata['validation_accuracy'] = best_accuracy
    
    def _compute_accuracy(
        self,
        data: List[Dict[str, Any]],
        candidates: List[Any]
    ) -> float:
        """
        Compute accuracy on data.
        
        Args:
            data: Examples to evaluate
            candidates: List of candidates
            
        Returns:
            Accuracy (fraction correct)
        """
        correct = 0
        total = len(data)
        
        for example in data:
            context = example['context']
            true_outcome = example['outcome']
            
            # Get ensemble prediction
            scores = self.score_all(candidates, context)
            predicted = candidates[np.argmax(scores)]
            
            if predicted == true_outcome:
                correct += 1
        
        return correct / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        base_dict = super().to_dict()
        
        base_dict.update({
            'num_scorers': self.num_scorers,
            'weights': self.weights.tolist(),
            'combination': self.combination,
            'scorers': [scorer.to_dict() for scorer in self.scorers]
        })
        
        return base_dict
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'EnsembleScorer':
        """Load from dictionary."""
        # Reconstruct base scorers
        # Note: This requires knowing the scorer types
        # For now, we'll raise NotImplementedError
        # In practice, you'd need a scorer registry
        raise NotImplementedError(
            "EnsembleScorer.from_dict requires scorer type registry. "
            "Reconstruct scorers manually and create new ensemble."
        )
