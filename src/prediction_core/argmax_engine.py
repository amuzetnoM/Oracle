"""
Argmax Engine - Core implementation of the argmax equation.

This is the heart of the prediction system:
    ŷ = argmax_{x ∈ C} S(x | c)

The engine selects the candidate with the highest score.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from .candidate_space import CandidateSpace
from .scoring.base_scorer import BaseScorer


class ArgmaxEngine:
    """
    Core argmax prediction engine.
    
    Implements: ŷ = argmax_{x ∈ C} S(x | c)
    
    Given a context and a scoring function, selects the
    best candidate from the candidate space.
    """
    
    def __init__(
        self,
        candidate_space: CandidateSpace,
        scorer: BaseScorer,
        return_scores: bool = False
    ):
        """
        Initialize argmax engine.
        
        Args:
            candidate_space: The candidate space C
            scorer: Scoring function S(x | c)
            return_scores: Whether to return scores along with prediction
        """
        self.candidate_space = candidate_space
        self.scorer = scorer
        self.return_scores = return_scores
        
        # Cache candidates list
        self.candidates = candidate_space.get_candidates()
    
    def predict(
        self,
        context: np.ndarray,
        return_all_scores: bool = False
    ) -> Union[Any, Tuple[Any, float], Tuple[Any, float, Dict[Any, float]]]:
        """
        Make a prediction given context.
        
        Computes: ŷ = argmax_{x ∈ C} S(x | c)
        
        Args:
            context: Context vector
            return_all_scores: If True, return scores for all candidates
            
        Returns:
            If return_all_scores=False:
                - prediction (if return_scores=False)
                - (prediction, best_score) (if return_scores=True)
            If return_all_scores=True:
                - (prediction, best_score, all_scores_dict)
        """
        # Compute scores for all candidates
        scores = self.scorer.score_all(self.candidates, context)
        
        # Find argmax
        best_idx = np.argmax(scores)
        prediction = self.candidates[best_idx]
        best_score = scores[best_idx]
        
        if return_all_scores:
            all_scores = {
                candidate: score
                for candidate, score in zip(self.candidates, scores)
            }
            return prediction, best_score, all_scores
        
        elif self.return_scores:
            return prediction, best_score
        
        else:
            return prediction
    
    def predict_top_k(
        self,
        context: np.ndarray,
        k: int = 3
    ) -> List[Tuple[Any, float]]:
        """
        Get top-k predictions with scores.
        
        Args:
            context: Context vector
            k: Number of top predictions to return
            
        Returns:
            List of (candidate, score) tuples, sorted by score descending
        """
        # Compute scores
        scores = self.scorer.score_all(self.candidates, context)
        
        # Get top k indices
        k = min(k, len(self.candidates))
        top_k_indices = np.argsort(scores)[-k:][::-1]
        
        # Return candidates and scores
        results = [
            (self.candidates[idx], scores[idx])
            for idx in top_k_indices
        ]
        
        return results
    
    def predict_with_confidence(
        self,
        context: np.ndarray,
        confidence_method: str = "score"
    ) -> Tuple[Any, float]:
        """
        Make prediction with confidence estimate.
        
        Args:
            context: Context vector
            confidence_method: How to compute confidence
                - "score": Use raw score
                - "normalized": Use score normalized by sum
                - "margin": Use margin between top two candidates
                
        Returns:
            (prediction, confidence) tuple
        """
        # Get all scores
        scores = self.scorer.score_all(self.candidates, context)
        
        # Find best
        best_idx = np.argmax(scores)
        prediction = self.candidates[best_idx]
        
        if confidence_method == "score":
            confidence = scores[best_idx]
        
        elif confidence_method == "normalized":
            total_score = np.sum(scores)
            confidence = scores[best_idx] / total_score if total_score > 0 else 0.0
        
        elif confidence_method == "margin":
            # Margin = difference between top two scores
            sorted_scores = np.sort(scores)
            if len(sorted_scores) >= 2:
                margin = sorted_scores[-1] - sorted_scores[-2]
                # Normalize margin to [0, 1]
                confidence = margin / (sorted_scores[-1] + 1e-10)
            else:
                confidence = 1.0
        
        else:
            raise ValueError(f"Unknown confidence method: {confidence_method}")
        
        return prediction, confidence
    
    def evaluate(
        self,
        test_data: List[Dict[str, Any]],
        metrics: List[str] = ["accuracy"]
    ) -> Dict[str, float]:
        """
        Evaluate engine on test data.
        
        Args:
            test_data: List of examples with 'context' and 'outcome'
            metrics: List of metrics to compute
            
        Returns:
            Dictionary of metric values
        """
        if not test_data:
            return {}
        
        predictions = []
        actuals = []
        scores = []
        
        for example in test_data:
            context = example['context']
            actual = example['outcome']
            
            pred, score, _ = self.predict(context, return_all_scores=True)
            
            predictions.append(pred)
            actuals.append(actual)
            scores.append(score)
        
        results = {}
        
        if "accuracy" in metrics:
            correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
            results['accuracy'] = correct / len(test_data)
        
        if "average_score" in metrics:
            results['average_score'] = np.mean(scores)
        
        if "top_3_accuracy" in metrics:
            # Check if actual is in top 3 predictions
            top_3_correct = 0
            for example in test_data:
                context = example['context']
                actual = example['outcome']
                top_3 = self.predict_top_k(context, k=3)
                if actual in [candidate for candidate, _ in top_3]:
                    top_3_correct += 1
            results['top_3_accuracy'] = top_3_correct / len(test_data)
        
        return results
    
    def get_score_distribution(self, context: np.ndarray) -> Dict[Any, float]:
        """
        Get probability distribution over all candidates.
        
        Args:
            context: Context vector
            
        Returns:
            Dictionary mapping candidates to scores
        """
        scores = self.scorer.score_all(self.candidates, context)
        
        return {
            candidate: score
            for candidate, score in zip(self.candidates, scores)
        }
    
    def update_scorer(self, context: np.ndarray, outcome: Any):
        """
        Update scorer with new observation.
        
        Args:
            context: Context vector
            outcome: Observed outcome
        """
        self.scorer.update(context, outcome)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine to dictionary."""
        return {
            'candidate_space': self.candidate_space.to_dict(),
            'scorer': self.scorer.to_dict(),
            'return_scores': self.return_scores
        }
