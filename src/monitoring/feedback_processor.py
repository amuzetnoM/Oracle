"""
Feedback Processor

Processes outcomes and feedback to improve model performance.
Implements learning from prediction results.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class FeedbackProcessor:
    """
    Process prediction outcomes for continuous learning.
    
    Analyzes prediction accuracy and updates model parameters.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        min_samples_for_update: int = 100
    ):
        """
        Initialize feedback processor.
        
        Args:
            learning_rate: Learning rate for updates
            min_samples_for_update: Minimum samples before updating
        """
        self.learning_rate = learning_rate
        self.min_samples_for_update = min_samples_for_update
        
        # Store feedback history
        self.feedback_history: List[Dict] = []
        
        # Performance by context
        self.context_performance: Dict = defaultdict(lambda: {
            'correct': 0,
            'total': 0,
            'avg_confidence': 0.0
        })
    
    def add_feedback(
        self,
        prediction: str,
        actual: str,
        confidence: float,
        context: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Add feedback from a prediction outcome.
        
        Args:
            prediction: Predicted outcome
            actual: Actual outcome
            confidence: Prediction confidence
            context: Context features
            timestamp: Feedback timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        correct = (prediction == actual)
        
        feedback = {
            'timestamp': timestamp,
            'prediction': prediction,
            'actual': actual,
            'correct': correct,
            'confidence': confidence,
            'context': context or {}
        }
        
        self.feedback_history.append(feedback)
        
        # Update context performance
        if context:
            context_key = self._context_to_key(context)
            perf = self.context_performance[context_key]
            perf['correct'] += int(correct)
            perf['total'] += 1
            # Update running average of confidence
            perf['avg_confidence'] = (
                (perf['avg_confidence'] * (perf['total'] - 1) + confidence) /
                perf['total']
            )
    
    def _context_to_key(self, context: Dict) -> str:
        """Convert context dict to hashable key."""
        # Simplified: use sorted items
        return str(sorted(context.items()))
    
    def get_accuracy_by_confidence(
        self,
        confidence_bins: int = 10
    ) -> Dict[str, List]:
        """
        Get accuracy broken down by confidence level.
        
        Args:
            confidence_bins: Number of confidence bins
        
        Returns:
            Dictionary with binned accuracy
        """
        if not self.feedback_history:
            return {'bins': [], 'accuracy': [], 'count': []}
        
        bins = np.linspace(0, 1, confidence_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        accuracy_by_bin = []
        count_by_bin = []
        
        for i in range(len(bins) - 1):
            feedback_in_bin = [
                f for f in self.feedback_history
                if bins[i] <= f['confidence'] < bins[i+1]
            ]
            
            if feedback_in_bin:
                accuracy = sum(f['correct'] for f in feedback_in_bin) / len(feedback_in_bin)
                accuracy_by_bin.append(accuracy)
                count_by_bin.append(len(feedback_in_bin))
            else:
                accuracy_by_bin.append(0.0)
                count_by_bin.append(0)
        
        return {
            'bins': bin_centers.tolist(),
            'accuracy': accuracy_by_bin,
            'count': count_by_bin
        }
    
    def get_calibration_error(self) -> float:
        """
        Calculate expected calibration error (ECE).
        
        Measures how well confidence scores match actual accuracy.
        
        Returns:
            Expected calibration error (0-1, lower is better)
        """
        calibration = self.get_accuracy_by_confidence()
        
        if not calibration['bins']:
            return 0.0
        
        # Weighted average of |confidence - accuracy|
        total_samples = sum(calibration['count'])
        if total_samples == 0:
            return 0.0
        
        ece = 0.0
        for conf, acc, count in zip(
            calibration['bins'],
            calibration['accuracy'],
            calibration['count']
        ):
            if count > 0:
                weight = count / total_samples
                ece += weight * abs(conf - acc)
        
        return ece
    
    def get_confidence_adjustment(self) -> float:
        """
        Calculate confidence adjustment factor.
        
        If model is overconfident (confidence > accuracy), return < 1.
        If model is underconfident (confidence < accuracy), return > 1.
        
        Returns:
            Adjustment factor to apply to confidences
        """
        if len(self.feedback_history) < self.min_samples_for_update:
            return 1.0
        
        avg_confidence = np.mean([f['confidence'] for f in self.feedback_history])
        accuracy = sum(f['correct'] for f in self.feedback_history) / len(self.feedback_history)
        
        if avg_confidence == 0:
            return 1.0
        
        # Adjustment factor
        adjustment = accuracy / avg_confidence
        
        # Limit adjustment to reasonable range
        adjustment = max(0.5, min(1.5, adjustment))
        
        return adjustment
    
    def get_performance_by_time(
        self,
        window_hours: int = 24
    ) -> List[Dict]:
        """
        Get performance metrics over time windows.
        
        Args:
            window_hours: Size of time window in hours
        
        Returns:
            List of performance by time window
        """
        if not self.feedback_history:
            return []
        
        # Group by time windows
        windows = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for feedback in self.feedback_history:
            # Round timestamp to window
            window_start = feedback['timestamp'].replace(
                minute=0, second=0, microsecond=0
            )
            window_key = window_start.isoformat()
            
            windows[window_key]['total'] += 1
            if feedback['correct']:
                windows[window_key]['correct'] += 1
        
        # Convert to list
        result = []
        for window_key, stats in sorted(windows.items()):
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            result.append({
                'timestamp': window_key,
                'accuracy': accuracy,
                'count': stats['total']
            })
        
        return result
    
    def identify_weak_contexts(
        self,
        threshold_accuracy: float = 0.5
    ) -> List[Tuple[str, Dict]]:
        """
        Identify contexts where model performs poorly.
        
        Args:
            threshold_accuracy: Accuracy threshold for weakness
        
        Returns:
            List of (context_key, performance_dict) tuples
        """
        weak_contexts = []
        
        for context_key, perf in self.context_performance.items():
            if perf['total'] >= self.min_samples_for_update:
                accuracy = perf['correct'] / perf['total']
                if accuracy < threshold_accuracy:
                    weak_contexts.append((context_key, {
                        'accuracy': accuracy,
                        'count': perf['total'],
                        'avg_confidence': perf['avg_confidence']
                    }))
        
        # Sort by worst accuracy
        weak_contexts.sort(key=lambda x: x[1]['accuracy'])
        
        return weak_contexts
    
    def should_retrain(
        self,
        accuracy_threshold: float = 0.6,
        recent_window: int = 100
    ) -> Tuple[bool, Dict]:
        """
        Determine if model should be retrained.
        
        Args:
            accuracy_threshold: Minimum acceptable accuracy
            recent_window: Number of recent predictions to check
        
        Returns:
            Tuple of (should_retrain, reasons_dict)
        """
        if len(self.feedback_history) < self.min_samples_for_update:
            return False, {'reason': 'insufficient_samples'}
        
        # Get recent feedback
        recent_feedback = self.feedback_history[-recent_window:]
        recent_accuracy = sum(f['correct'] for f in recent_feedback) / len(recent_feedback)
        
        reasons = {}
        should_retrain = False
        
        # Check accuracy
        if recent_accuracy < accuracy_threshold:
            should_retrain = True
            reasons['low_accuracy'] = recent_accuracy
        
        # Check calibration
        calibration_error = self.get_calibration_error()
        if calibration_error > 0.2:  # High miscalibration
            should_retrain = True
            reasons['poor_calibration'] = calibration_error
        
        # Check for trend
        if len(self.feedback_history) >= 200:
            first_half = self.feedback_history[:len(self.feedback_history)//2]
            second_half = self.feedback_history[len(self.feedback_history)//2:]
            
            first_accuracy = sum(f['correct'] for f in first_half) / len(first_half)
            second_accuracy = sum(f['correct'] for f in second_half) / len(second_half)
            
            if second_accuracy < first_accuracy * 0.9:  # 10% degradation
                should_retrain = True
                reasons['performance_degradation'] = {
                    'first_half': first_accuracy,
                    'second_half': second_accuracy
                }
        
        return should_retrain, reasons
    
    def get_summary(self) -> Dict:
        """
        Get comprehensive feedback summary.
        
        Returns:
            Dictionary with feedback statistics
        """
        if not self.feedback_history:
            return {
                'total_feedback': 0,
                'accuracy': 0.0,
                'avg_confidence': 0.0,
                'calibration_error': 0.0
            }
        
        accuracy = sum(f['correct'] for f in self.feedback_history) / len(self.feedback_history)
        avg_confidence = np.mean([f['confidence'] for f in self.feedback_history])
        
        return {
            'total_feedback': len(self.feedback_history),
            'accuracy': accuracy,
            'avg_confidence': avg_confidence,
            'calibration_error': self.get_calibration_error(),
            'confidence_adjustment': self.get_confidence_adjustment()
        }
