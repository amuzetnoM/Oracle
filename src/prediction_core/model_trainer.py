"""
Model Trainer - Trains scoring functions on historical data.

Handles:
- Data preparation and validation
- Training scorer models
- Cross-validation
- Hyperparameter tuning
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from .scoring.base_scorer import BaseScorer
from .candidate_space import CandidateSpace


class ModelTrainer:
    """
    Trains and validates scoring functions.
    
    Provides utilities for training scorers on historical data
    with proper validation and performance tracking.
    """
    
    def __init__(
        self,
        candidate_space: CandidateSpace,
        validation_split: float = 0.2,
        random_seed: int = 42
    ):
        """
        Initialize model trainer.
        
        Args:
            candidate_space: Candidate space for predictions
            validation_split: Fraction of data to use for validation
            random_seed: Random seed for reproducibility
        """
        self.candidate_space = candidate_space
        self.validation_split = validation_split
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
        
        # Training history
        self.training_history = []
    
    def prepare_data(
        self,
        contexts: np.ndarray,
        outcomes: List[Any],
        shuffle: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Prepare training data from raw contexts and outcomes.
        
        Args:
            contexts: Array of context vectors (n_samples, n_features)
            outcomes: List of outcomes (n_samples,)
            shuffle: Whether to shuffle the data
            
        Returns:
            List of training examples
        """
        if len(contexts) != len(outcomes):
            raise ValueError("Contexts and outcomes must have same length")
        
        # Create examples
        examples = [
            {'context': context, 'outcome': outcome}
            for context, outcome in zip(contexts, outcomes)
        ]
        
        # Shuffle if requested
        if shuffle:
            indices = np.random.permutation(len(examples))
            examples = [examples[i] for i in indices]
        
        return examples
    
    def split_data(
        self,
        data: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split data into training and validation sets.
        
        Args:
            data: Full dataset
            
        Returns:
            (train_data, val_data) tuple
        """
        n_samples = len(data)
        n_val = int(n_samples * self.validation_split)
        
        val_data = data[:n_val]
        train_data = data[n_val:]
        
        return train_data, val_data
    
    def train(
        self,
        scorer: BaseScorer,
        training_data: List[Dict[str, Any]],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Train a scorer on data.
        
        Args:
            scorer: Scorer to train
            training_data: Training examples
            validate: Whether to perform validation
            
        Returns:
            Training metrics
        """
        if validate and len(training_data) > 10:
            # Split data
            train_data, val_data = self.split_data(training_data)
        else:
            train_data = training_data
            val_data = None
        
        # Train scorer
        scorer.train(train_data)
        
        # Compute metrics
        metrics = {
            'num_train_examples': len(train_data),
            'scorer_name': scorer.name
        }
        
        # Validation metrics
        if val_data is not None:
            val_metrics = self._evaluate_scorer(scorer, val_data)
            metrics['validation'] = val_metrics
        
        # Store in history
        self.training_history.append(metrics)
        
        return metrics
    
    def _evaluate_scorer(
        self,
        scorer: BaseScorer,
        data: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Evaluate scorer on data.
        
        Args:
            scorer: Trained scorer
            data: Evaluation data
            
        Returns:
            Evaluation metrics
        """
        candidates = self.candidate_space.get_candidates()
        
        correct = 0
        total = len(data)
        scores_list = []
        
        for example in data:
            context = example['context']
            true_outcome = example['outcome']
            
            # Get prediction
            scores = scorer.score_all(candidates, context)
            predicted_idx = np.argmax(scores)
            predicted = candidates[predicted_idx]
            
            if predicted == true_outcome:
                correct += 1
            
            scores_list.append(scores[predicted_idx])
        
        metrics = {
            'accuracy': correct / total if total > 0 else 0.0,
            'average_score': np.mean(scores_list) if scores_list else 0.0,
            'num_examples': total
        }
        
        return metrics
    
    def cross_validate(
        self,
        scorer: BaseScorer,
        data: List[Dict[str, Any]],
        n_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Perform k-fold cross-validation.
        
        Args:
            scorer: Scorer to validate
            data: Full dataset
            n_folds: Number of folds
            
        Returns:
            Cross-validation results
        """
        n_samples = len(data)
        fold_size = n_samples // n_folds
        
        fold_metrics = []
        
        for fold in range(n_folds):
            # Create fold split
            val_start = fold * fold_size
            val_end = (fold + 1) * fold_size if fold < n_folds - 1 else n_samples
            
            val_data = data[val_start:val_end]
            train_data = data[:val_start] + data[val_end:]
            
            # Train on fold
            scorer.train(train_data)
            
            # Evaluate
            metrics = self._evaluate_scorer(scorer, val_data)
            metrics['fold'] = fold
            fold_metrics.append(metrics)
        
        # Aggregate results
        accuracies = [m['accuracy'] for m in fold_metrics]
        avg_scores = [m['average_score'] for m in fold_metrics]
        
        results = {
            'n_folds': n_folds,
            'fold_metrics': fold_metrics,
            'mean_accuracy': np.mean(accuracies),
            'std_accuracy': np.std(accuracies),
            'mean_score': np.mean(avg_scores),
            'std_score': np.std(avg_scores)
        }
        
        return results
    
    def compare_scorers(
        self,
        scorers: List[BaseScorer],
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple scorers on same data.
        
        Args:
            scorers: List of scorers to compare
            data: Evaluation data
            
        Returns:
            Comparison results
        """
        results = {}
        
        train_data, val_data = self.split_data(data)
        
        for scorer in scorers:
            # Train
            scorer.train(train_data)
            
            # Evaluate
            metrics = self._evaluate_scorer(scorer, val_data)
            results[scorer.name] = metrics
        
        # Find best scorer
        best_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        results['best_scorer'] = best_name
        
        return results
    
    def get_training_history(self) -> List[Dict[str, Any]]:
        """
        Get training history.
        
        Returns:
            List of training metrics from all training runs
        """
        return self.training_history
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'validation_split': self.validation_split,
            'random_seed': self.random_seed,
            'training_history': self.training_history
        }
