"""
Confidence Calculator - Computes confidence metrics for predictions.

Provides various methods to quantify prediction confidence:
- Score-based: Raw score values
- Entropy-based: Shannon entropy of distribution
- Margin-based: Difference between top candidates
- Calibration-based: Historical accuracy by score range
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from collections import defaultdict


class ConfidenceCalculator:
    """
    Calculates confidence metrics for predictions.
    
    Confidence indicates how certain the system is about a prediction.
    Higher confidence suggests the prediction is more reliable.
    """
    
    def __init__(self, calibration_bins: int = 10):
        """
        Initialize confidence calculator.
        
        Args:
            calibration_bins: Number of bins for calibration analysis
        """
        self.calibration_bins = calibration_bins
        
        # Calibration data: maps score bins to (correct, total) counts
        self.calibration_data = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        # Statistics
        self.total_predictions = 0
        self.correct_predictions = 0
    
    def compute_score_confidence(self, score: float) -> float:
        """
        Compute confidence from raw score.
        
        Assumes scores are in [0, 1] range (probabilities).
        
        Args:
            score: Score of the predicted candidate
            
        Returns:
            Confidence in [0, 1]
        """
        # Clip to valid range
        return np.clip(score, 0.0, 1.0)
    
    def compute_normalized_confidence(
        self,
        scores: np.ndarray,
        predicted_idx: int
    ) -> float:
        """
        Compute confidence from normalized score distribution.
        
        Confidence = P(predicted) / sum(P(all))
        
        Args:
            scores: Array of scores for all candidates
            predicted_idx: Index of predicted candidate
            
        Returns:
            Normalized confidence
        """
        total = np.sum(scores)
        if total > 0:
            return scores[predicted_idx] / total
        else:
            return 1.0 / len(scores)
    
    def compute_entropy_confidence(self, scores: np.ndarray) -> float:
        """
        Compute confidence from entropy of score distribution.
        
        Lower entropy = higher confidence (more concentrated distribution)
        
        Confidence = 1 - normalized_entropy
        
        Args:
            scores: Array of scores for all candidates
            
        Returns:
            Entropy-based confidence in [0, 1]
        """
        # Normalize to probabilities
        probs = scores / (np.sum(scores) + 1e-10)
        
        # Compute Shannon entropy
        # H = -Σ p(x) * log(p(x))
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        
        # Maximum entropy (uniform distribution)
        max_entropy = np.log(len(scores))
        
        # Normalize to [0, 1]
        if max_entropy > 0:
            normalized_entropy = entropy / max_entropy
            confidence = 1.0 - normalized_entropy
        else:
            confidence = 1.0
        
        return confidence
    
    def compute_margin_confidence(
        self,
        scores: np.ndarray,
        predicted_idx: int
    ) -> float:
        """
        Compute confidence from margin between top candidates.
        
        Larger margin = higher confidence
        
        Confidence = (score_1 - score_2) / score_1
        
        Args:
            scores: Array of scores for all candidates
            predicted_idx: Index of predicted candidate
            
        Returns:
            Margin-based confidence in [0, 1]
        """
        sorted_scores = np.sort(scores)[::-1]  # Descending order
        
        if len(sorted_scores) < 2:
            return 1.0
        
        top_score = sorted_scores[0]
        second_score = sorted_scores[1]
        
        if top_score > 0:
            margin = (top_score - second_score) / top_score
            return np.clip(margin, 0.0, 1.0)
        else:
            return 0.0
    
    def compute_ratio_confidence(self, scores: np.ndarray) -> float:
        """
        Compute confidence from ratio of top to second score.
        
        Confidence = score_1 / (score_1 + score_2)
        
        Args:
            scores: Array of scores for all candidates
            
        Returns:
            Ratio-based confidence in [0, 1]
        """
        sorted_scores = np.sort(scores)[::-1]
        
        if len(sorted_scores) < 2:
            return 1.0
        
        top_score = sorted_scores[0]
        second_score = sorted_scores[1]
        
        total = top_score + second_score
        if total > 0:
            return top_score / total
        else:
            return 0.5
    
    def compute_combined_confidence(
        self,
        scores: np.ndarray,
        predicted_idx: int,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compute combined confidence using multiple methods.
        
        Args:
            scores: Array of scores for all candidates
            predicted_idx: Index of predicted candidate
            weights: Weights for each method (default: equal weights)
            
        Returns:
            Combined confidence
        """
        if weights is None:
            weights = {
                'score': 0.25,
                'normalized': 0.25,
                'entropy': 0.25,
                'margin': 0.25
            }
        
        confidences = {}
        
        if 'score' in weights:
            confidences['score'] = self.compute_score_confidence(scores[predicted_idx])
        
        if 'normalized' in weights:
            confidences['normalized'] = self.compute_normalized_confidence(scores, predicted_idx)
        
        if 'entropy' in weights:
            confidences['entropy'] = self.compute_entropy_confidence(scores)
        
        if 'margin' in weights:
            confidences['margin'] = self.compute_margin_confidence(scores, predicted_idx)
        
        if 'ratio' in weights:
            confidences['ratio'] = self.compute_ratio_confidence(scores)
        
        # Weighted average
        combined = sum(
            weights.get(method, 0) * confidence
            for method, confidence in confidences.items()
        )
        
        return combined
    
    def update_calibration(
        self,
        score: float,
        was_correct: bool
    ):
        """
        Update calibration data with new observation.
        
        Args:
            score: Confidence score of the prediction
            was_correct: Whether prediction was correct
        """
        # Determine which bin this score falls into
        bin_idx = int(score * self.calibration_bins)
        bin_idx = min(bin_idx, self.calibration_bins - 1)
        
        # Update counts
        self.calibration_data[bin_idx]['total'] += 1
        if was_correct:
            self.calibration_data[bin_idx]['correct'] += 1
        
        # Update overall statistics
        self.total_predictions += 1
        if was_correct:
            self.correct_predictions += 1
    
    def get_calibrated_confidence(self, score: float) -> float:
        """
        Get calibrated confidence based on historical accuracy.
        
        Returns the empirical accuracy for predictions with similar scores.
        
        Args:
            score: Raw confidence score
            
        Returns:
            Calibrated confidence (historical accuracy)
        """
        # Find bin
        bin_idx = int(score * self.calibration_bins)
        bin_idx = min(bin_idx, self.calibration_bins - 1)
        
        # Get calibration data for this bin
        data = self.calibration_data[bin_idx]
        
        if data['total'] > 0:
            # Return empirical accuracy
            return data['correct'] / data['total']
        else:
            # No data - return raw score
            return score
    
    def get_calibration_curve(self) -> Tuple[List[float], List[float]]:
        """
        Get calibration curve data.
        
        Returns:
            (predicted_probabilities, empirical_accuracies) tuple
        """
        predicted_probs = []
        empirical_accs = []
        
        for bin_idx in range(self.calibration_bins):
            # Bin center
            predicted_prob = (bin_idx + 0.5) / self.calibration_bins
            
            # Empirical accuracy
            data = self.calibration_data[bin_idx]
            if data['total'] > 0:
                empirical_acc = data['correct'] / data['total']
            else:
                empirical_acc = None
            
            if empirical_acc is not None:
                predicted_probs.append(predicted_prob)
                empirical_accs.append(empirical_acc)
        
        return predicted_probs, empirical_accs
    
    def compute_expected_calibration_error(self) -> float:
        """
        Compute Expected Calibration Error (ECE).
        
        ECE = Σ (|accuracy_i - confidence_i|) * (n_i / n)
        
        Returns:
            ECE value
        """
        if self.total_predictions == 0:
            return 0.0
        
        ece = 0.0
        
        for bin_idx in range(self.calibration_bins):
            data = self.calibration_data[bin_idx]
            
            if data['total'] > 0:
                # Bin confidence (center)
                confidence = (bin_idx + 0.5) / self.calibration_bins
                
                # Empirical accuracy
                accuracy = data['correct'] / data['total']
                
                # Weighted difference
                weight = data['total'] / self.total_predictions
                ece += abs(accuracy - confidence) * weight
        
        return ece
    
    def get_accuracy(self) -> float:
        """
        Get overall prediction accuracy.
        
        Returns:
            Accuracy (fraction correct)
        """
        if self.total_predictions > 0:
            return self.correct_predictions / self.total_predictions
        else:
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'calibration_bins': self.calibration_bins,
            'calibration_data': {
                str(k): v for k, v in self.calibration_data.items()
            },
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions
        }
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ConfidenceCalculator':
        """Load from dictionary."""
        calc = cls(calibration_bins=config['calibration_bins'])
        
        calc.calibration_data = defaultdict(
            lambda: {'correct': 0, 'total': 0},
            {int(k): v for k, v in config['calibration_data'].items()}
        )
        calc.total_predictions = config['total_predictions']
        calc.correct_predictions = config['correct_predictions']
        
        return calc
