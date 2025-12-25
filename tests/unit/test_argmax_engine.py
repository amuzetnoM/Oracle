"""
Unit tests for ArgmaxEngine.
"""

import pytest
import numpy as np
from src.prediction_core import (
    ArgmaxEngine,
    CandidateSpace,
    Direction
)
from src.prediction_core.scoring import StatisticalScorer


class TestArgmaxEngine:
    """Test suite for ArgmaxEngine."""
    
    def test_initialization(self):
        """Test engine initialization."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        engine = ArgmaxEngine(
            candidate_space=cs,
            scorer=scorer
        )
        
        assert engine.candidate_space == cs
        assert engine.scorer == scorer
        assert len(engine.candidates) == 3
    
    def test_predict(self):
        """Test basic prediction."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        # Train scorer
        training_data = [
            {'context': np.array([1.0, 2.0]), 'outcome': Direction.UP},
            {'context': np.array([1.1, 2.1]), 'outcome': Direction.UP},
            {'context': np.array([-1.0, -2.0]), 'outcome': Direction.DOWN},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        # Predict on context similar to UP
        prediction = engine.predict(np.array([1.0, 2.0]))
        
        assert prediction == Direction.UP
    
    def test_predict_with_scores(self):
        """Test prediction with score return."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(
            candidate_space=cs,
            scorer=scorer,
            return_scores=True
        )
        
        prediction, score = engine.predict(np.array([1.0]))
        
        assert prediction == Direction.UP
        assert score > 0
    
    def test_predict_all_scores(self):
        """Test getting all candidate scores."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        prediction, score, all_scores = engine.predict(
            np.array([1.0]),
            return_all_scores=True
        )
        
        assert isinstance(all_scores, dict)
        assert Direction.UP in all_scores
        assert Direction.DOWN in all_scores
        assert Direction.FLAT in all_scores
    
    def test_predict_top_k(self):
        """Test top-k predictions."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        top_k = engine.predict_top_k(np.array([1.0]), k=2)
        
        assert len(top_k) == 2
        assert top_k[0][0] == Direction.UP  # Top prediction
        assert top_k[0][1] > top_k[1][1]  # Scores descending
    
    def test_predict_with_confidence(self):
        """Test prediction with confidence."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([1.0]), 'outcome': Direction.UP},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        prediction, confidence = engine.predict_with_confidence(
            np.array([1.0]),
            confidence_method="normalized"
        )
        
        assert prediction == Direction.UP
        assert 0 <= confidence <= 1
    
    def test_evaluate(self):
        """Test evaluation on test data."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        test_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
            {'context': np.array([-1.0]), 'outcome': Direction.DOWN},
        ]
        
        metrics = engine.evaluate(test_data, metrics=["accuracy"])
        
        assert 'accuracy' in metrics
        assert 0 <= metrics['accuracy'] <= 1
    
    def test_get_score_distribution(self):
        """Test getting score distribution."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        distribution = engine.get_score_distribution(np.array([1.0]))
        
        assert isinstance(distribution, dict)
        assert len(distribution) == 3
        assert all(c in distribution for c in cs.candidates)
    
    def test_update_scorer(self):
        """Test online scorer update."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        training_data = [
            {'context': np.array([1.0]), 'outcome': Direction.UP},
        ]
        scorer.train(training_data)
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        initial_obs = scorer.total_observations
        
        # Update with new observation
        engine.update_scorer(np.array([2.0]), Direction.DOWN)
        
        assert scorer.total_observations == initial_obs + 1
    
    def test_serialization(self):
        """Test to_dict serialization."""
        cs = CandidateSpace(candidate_type="direction")
        scorer = StatisticalScorer()
        
        engine = ArgmaxEngine(candidate_space=cs, scorer=scorer)
        
        config = engine.to_dict()
        
        assert 'candidate_space' in config
        assert 'scorer' in config
        assert 'return_scores' in config
