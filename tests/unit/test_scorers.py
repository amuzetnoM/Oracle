"""
Unit tests for scoring functions.
"""

import pytest
import numpy as np
from src.prediction_core.scoring import (
    StatisticalScorer,
    BayesianScorer,
    EnsembleScorer
)
from src.prediction_core import Direction


class TestStatisticalScorer:
    """Test suite for StatisticalScorer."""
    
    def test_initialization(self):
        """Test scorer initialization."""
        scorer = StatisticalScorer(context_bins=10, smoothing_alpha=1.0)
        
        assert scorer.context_bins == 10
        assert scorer.smoothing_alpha == 1.0
        assert not scorer.is_trained
    
    def test_training(self):
        """Test training the scorer."""
        scorer = StatisticalScorer()
        
        # Create simple training data
        training_data = [
            {'context': np.array([1.0, 2.0]), 'outcome': Direction.UP},
            {'context': np.array([1.1, 2.1]), 'outcome': Direction.UP},
            {'context': np.array([-1.0, -2.0]), 'outcome': Direction.DOWN},
            {'context': np.array([-1.1, -2.1]), 'outcome': Direction.DOWN},
        ]
        
        scorer.train(training_data)
        
        assert scorer.is_trained
        assert scorer.num_candidates == 2
        assert scorer.total_observations == 4
    
    def test_scoring(self):
        """Test scoring candidates."""
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0, 2.0]), 'outcome': Direction.UP},
            {'context': np.array([1.1, 2.1]), 'outcome': Direction.UP},
            {'context': np.array([-1.0, -2.0]), 'outcome': Direction.DOWN},
        ]
        
        scorer.train(training_data)
        
        # Test on similar context to UP
        score_up = scorer.score(Direction.UP, np.array([1.0, 2.0]))
        score_down = scorer.score(Direction.DOWN, np.array([1.0, 2.0]))
        
        # UP should have higher score for this context
        assert score_up > score_down
    
    def test_score_all(self):
        """Test scoring all candidates."""
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
            {'context': np.array([0.0]), 'outcome': Direction.FLAT},
        ]
        
        scorer.train(training_data)
        
        candidates = [Direction.UP, Direction.DOWN, Direction.FLAT]
        scores = scorer.score_all(candidates, np.array([1.0]))
        
        assert len(scores) == 3
        assert all(s >= 0 for s in scores)
    
    def test_online_update(self):
        """Test online learning with update."""
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
        ]
        
        scorer.train(training_data)
        initial_observations = scorer.total_observations
        
        # Update with new observation
        scorer.update(np.array([2.0]), Direction.DOWN)
        
        assert scorer.total_observations == initial_observations + 1


class TestBayesianScorer:
    """Test suite for BayesianScorer."""
    
    def test_initialization(self):
        """Test scorer initialization."""
        scorer = BayesianScorer(use_log_prob=True, prior_strength=1.0)
        
        assert scorer.use_log_prob
        assert scorer.prior_strength == 1.0
        assert not scorer.is_trained
    
    def test_training(self):
        """Test training the Bayesian scorer."""
        scorer = BayesianScorer()
        
        # Create training data with clear patterns
        training_data = [
            {'context': np.array([1.0, 2.0]), 'outcome': Direction.UP},
            {'context': np.array([1.1, 2.1]), 'outcome': Direction.UP},
            {'context': np.array([1.2, 2.2]), 'outcome': Direction.UP},
            {'context': np.array([-1.0, -2.0]), 'outcome': Direction.DOWN},
            {'context': np.array([-1.1, -2.1]), 'outcome': Direction.DOWN},
        ]
        
        scorer.train(training_data)
        
        assert scorer.is_trained
        assert scorer.num_candidates == 2
        assert Direction.UP in scorer.priors
        assert Direction.DOWN in scorer.priors
    
    def test_scoring(self):
        """Test Bayesian scoring."""
        scorer = BayesianScorer()
        
        training_data = [
            {'context': np.array([1.0, 2.0]), 'outcome': Direction.UP},
            {'context': np.array([1.1, 2.1]), 'outcome': Direction.UP},
            {'context': np.array([-1.0, -2.0]), 'outcome': Direction.DOWN},
            {'context': np.array([-1.1, -2.1]), 'outcome': Direction.DOWN},
        ]
        
        scorer.train(training_data)
        
        # Test on context similar to UP pattern
        score_up = scorer.score(Direction.UP, np.array([1.0, 2.0]))
        score_down = scorer.score(Direction.DOWN, np.array([1.0, 2.0]))
        
        # UP should have higher score
        assert score_up > score_down
    
    def test_posterior_distribution(self):
        """Test getting posterior distribution."""
        scorer = BayesianScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        
        scorer.train(training_data)
        
        dist = scorer.get_posterior_distribution(np.array([1.0]))
        
        assert isinstance(dist, dict)
        assert Direction.UP in dist
        assert Direction.DOWN in dist
        # Probabilities should sum to ~1
        assert abs(sum(dist.values()) - 1.0) < 0.01


class TestEnsembleScorer:
    """Test suite for EnsembleScorer."""
    
    def test_initialization(self):
        """Test ensemble initialization."""
        scorer1 = StatisticalScorer(name="stat1")
        scorer2 = BayesianScorer(name="bayes1")
        
        ensemble = EnsembleScorer(
            scorers=[scorer1, scorer2],
            combination="weighted_average"
        )
        
        assert ensemble.num_scorers == 2
        assert len(ensemble.weights) == 2
    
    def test_training(self):
        """Test training ensemble."""
        scorer1 = StatisticalScorer(name="stat1")
        scorer2 = BayesianScorer(name="bayes1")
        
        ensemble = EnsembleScorer(scorers=[scorer1, scorer2])
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        
        ensemble.train(training_data)
        
        assert ensemble.is_trained
        assert scorer1.is_trained
        assert scorer2.is_trained
    
    def test_weighted_average_scoring(self):
        """Test weighted average combination."""
        scorer1 = StatisticalScorer(name="stat1")
        scorer2 = BayesianScorer(name="bayes1")
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([1.1]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        
        scorer1.train(training_data)
        scorer2.train(training_data)
        
        ensemble = EnsembleScorer(
            scorers=[scorer1, scorer2],
            weights=[0.5, 0.5],
            combination="weighted_average"
        )
        ensemble.is_trained = True
        
        score = ensemble.score(Direction.UP, np.array([1.0]))
        assert score > 0
    
    def test_custom_weights(self):
        """Test custom weight assignment."""
        scorer1 = StatisticalScorer(name="stat1")
        scorer2 = BayesianScorer(name="bayes1")
        
        weights = [0.7, 0.3]
        ensemble = EnsembleScorer(
            scorers=[scorer1, scorer2],
            weights=weights
        )
        
        # Weights should be normalized
        assert abs(sum(ensemble.weights) - 1.0) < 1e-6
        assert ensemble.weights[0] == 0.7
        assert ensemble.weights[1] == 0.3
    
    def test_voting_combination(self):
        """Test voting combination strategy."""
        scorer1 = StatisticalScorer(name="stat1")
        scorer2 = BayesianScorer(name="bayes1")
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        
        scorer1.train(training_data)
        scorer2.train(training_data)
        
        ensemble = EnsembleScorer(
            scorers=[scorer1, scorer2],
            combination="voting"
        )
        ensemble.is_trained = True
        
        candidates = [Direction.UP, Direction.DOWN]
        scores = ensemble.score_all(candidates, np.array([1.0]))
        
        assert len(scores) == 2
        assert abs(sum(scores) - 1.0) < 1e-6
