"""
Bayesian Scorer - Probabilistic scoring using Bayesian estimation.

This scorer uses Bayesian inference to estimate P(x | c):
    P(x | c) ∝ P(c | x) * P(x)

Uses Gaussian Naive Bayes with prior and likelihood estimation.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from scipy.stats import norm
from .base_scorer import BaseScorer


class BayesianScorer(BaseScorer):
    """
    Bayesian probability estimator for scoring candidates.
    
    Uses Naive Bayes assumption: P(c | x) = ∏ P(c_i | x)
    Estimates P(c_i | x) as Gaussian distributions.
    
    Score: S(x | c) = P(x | c) = P(c | x) * P(x) / P(c)
    Since P(c) is constant across candidates, we compute:
        S(x | c) ∝ P(c | x) * P(x)
    """
    
    def __init__(
        self,
        name: str = "bayesian_scorer",
        use_log_prob: bool = True,
        prior_strength: float = 1.0,
        min_variance: float = 1e-6
    ):
        """
        Initialize Bayesian scorer.
        
        Args:
            name: Scorer name
            use_log_prob: Use log probabilities for numerical stability
            prior_strength: Strength of prior (pseudo-counts)
            min_variance: Minimum variance to prevent division by zero
        """
        super().__init__(name)
        self.use_log_prob = use_log_prob
        self.prior_strength = prior_strength
        self.min_variance = min_variance
        
        # Model parameters
        self.candidates = None
        self.num_candidates = 0
        self.context_dim = None
        
        # Prior probabilities P(x)
        self.priors = {}
        
        # Likelihood parameters: P(c_i | x) ~ N(μ, σ²)
        self.means = {}  # means[candidate] = array of means per feature
        self.variances = {}  # variances[candidate] = array of variances per feature
        
        # Training statistics
        self.total_observations = 0
    
    def train(self, training_data: List[Dict[str, Any]]):
        """
        Train Bayesian scorer on historical data.
        
        Estimates:
        - Prior probabilities P(x) from frequencies
        - Likelihood parameters P(c | x) as Gaussian per feature
        
        Args:
            training_data: List of examples with 'context' and 'outcome'
        """
        if not training_data:
            raise ValueError("Training data cannot be empty")
        
        # Extract contexts and outcomes
        contexts = np.array([example['context'] for example in training_data])
        outcomes = [example['outcome'] for example in training_data]
        
        self.context_dim = contexts.shape[1]
        self.total_observations = len(training_data)
        
        # Get unique candidates
        unique_candidates = list(set(outcomes))
        self.candidates = sorted(unique_candidates, key=str)
        self.num_candidates = len(self.candidates)
        
        # Estimate priors P(x)
        for candidate in self.candidates:
            count = sum(1 for outcome in outcomes if outcome == candidate)
            # Add prior strength for smoothing
            self.priors[candidate] = (count + self.prior_strength) / \
                                    (self.total_observations + self.prior_strength * self.num_candidates)
        
        # Estimate likelihoods P(c | x)
        for candidate in self.candidates:
            # Get all contexts where this candidate occurred
            candidate_contexts = contexts[np.array(outcomes) == candidate]
            
            if len(candidate_contexts) > 0:
                # Estimate mean and variance for each feature
                self.means[candidate] = np.mean(candidate_contexts, axis=0)
                self.variances[candidate] = np.var(candidate_contexts, axis=0)
                
                # Ensure minimum variance
                self.variances[candidate] = np.maximum(
                    self.variances[candidate],
                    self.min_variance
                )
            else:
                # No observations - use global statistics
                self.means[candidate] = np.mean(contexts, axis=0)
                self.variances[candidate] = np.var(contexts, axis=0) + self.min_variance
        
        self.is_trained = True
        
        # Store metadata
        self.metadata = {
            'num_examples': len(training_data),
            'num_candidates': self.num_candidates,
            'context_dim': self.context_dim,
            'use_log_prob': self.use_log_prob
        }
    
    def _compute_likelihood(self, candidate: Any, context: np.ndarray) -> float:
        """
        Compute likelihood P(c | x) for a candidate.
        
        Assumes features are independent (Naive Bayes):
            P(c | x) = ∏ P(c_i | x)
        
        Each P(c_i | x) is modeled as Gaussian.
        
        Args:
            candidate: Candidate to evaluate
            context: Context vector
            
        Returns:
            Likelihood value (or log-likelihood if use_log_prob=True)
        """
        if candidate not in self.means:
            # Unknown candidate
            return -np.inf if self.use_log_prob else 0.0
        
        mean = self.means[candidate]
        variance = self.variances[candidate]
        
        if self.use_log_prob:
            # Log probability for numerical stability
            log_prob = 0.0
            for i in range(len(context)):
                log_prob += norm.logpdf(context[i], loc=mean[i], scale=np.sqrt(variance[i]))
            return log_prob
        else:
            # Direct probability
            prob = 1.0
            for i in range(len(context)):
                prob *= norm.pdf(context[i], loc=mean[i], scale=np.sqrt(variance[i]))
            return prob
    
    def score(self, candidate: Any, context: np.ndarray) -> float:
        """
        Compute Bayesian score S(x | c) = P(x | c).
        
        Uses Bayes' rule:
            P(x | c) ∝ P(c | x) * P(x)
        
        Args:
            candidate: Candidate to score
            context: Context vector
            
        Returns:
            Score (unnormalized posterior probability)
        """
        if not self.is_trained:
            return 1.0 / max(1, self.num_candidates)
        
        self.validate_context(context)
        
        if candidate not in self.priors:
            return 0.0
        
        # Get prior
        prior = self.priors[candidate]
        
        # Get likelihood
        likelihood = self._compute_likelihood(candidate, context)
        
        if self.use_log_prob:
            # log P(x | c) = log P(c | x) + log P(x)
            log_score = likelihood + np.log(prior)
            # Convert back to probability for consistency
            return np.exp(log_score)
        else:
            # P(x | c) = P(c | x) * P(x)
            return likelihood * prior
    
    def score_all(self, candidates: List[Any], context: np.ndarray) -> np.ndarray:
        """
        Compute scores for all candidates and normalize.
        
        Args:
            candidates: List of candidates
            context: Context vector
            
        Returns:
            Array of normalized scores (probabilities)
        """
        # Compute unnormalized scores
        scores = np.array([self.score(c, context) for c in candidates])
        
        # Normalize to get proper probabilities
        total = np.sum(scores)
        if total > 0:
            scores = scores / total
        else:
            # Uniform if all scores are zero
            scores = np.ones(len(candidates)) / len(candidates)
        
        return scores
    
    def get_posterior_distribution(self, context: np.ndarray) -> Dict[Any, float]:
        """
        Get full posterior distribution P(x | c) for all candidates.
        
        Args:
            context: Context vector
            
        Returns:
            Dictionary mapping candidates to posterior probabilities
        """
        if not self.is_trained:
            return {}
        
        scores = self.score_all(self.candidates, context)
        
        distribution = {
            candidate: score
            for candidate, score in zip(self.candidates, scores)
        }
        
        return distribution
    
    def update(self, context: np.ndarray, outcome: Any):
        """
        Online Bayesian update (simplified).
        
        For true online Bayesian learning, would need full
        posterior update. Here we use a simple incremental update.
        
        Args:
            context: Context vector
            outcome: Observed outcome
        """
        if not self.is_trained:
            return
        
        self.validate_context(context)
        
        # Update prior
        if outcome in self.priors:
            # Incremental update
            alpha = 1.0 / (self.total_observations + 1)
            old_prior = self.priors[outcome]
            self.priors[outcome] = (1 - alpha) * old_prior + alpha
            
            # Normalize priors
            total_prior = sum(self.priors.values())
            for candidate in self.priors:
                self.priors[candidate] /= total_prior
        
        # Update likelihood parameters (running average)
        if outcome in self.means:
            alpha = 1.0 / (self.total_observations + 1)
            old_mean = self.means[outcome]
            self.means[outcome] = (1 - alpha) * old_mean + alpha * context
            
            # Update variance (simplified)
            diff = context - self.means[outcome]
            self.variances[outcome] = (1 - alpha) * self.variances[outcome] + \
                                     alpha * (diff ** 2)
            self.variances[outcome] = np.maximum(self.variances[outcome], self.min_variance)
        
        self.total_observations += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        base_dict = super().to_dict()
        
        base_dict.update({
            'use_log_prob': self.use_log_prob,
            'prior_strength': self.prior_strength,
            'min_variance': self.min_variance,
            'context_dim': self.context_dim,
            'total_observations': self.total_observations,
            'candidates': [str(c) for c in self.candidates] if self.candidates else None,
            'num_candidates': self.num_candidates,
            'priors': {str(k): float(v) for k, v in self.priors.items()},
            'means': {str(k): v.tolist() for k, v in self.means.items()},
            'variances': {str(k): v.tolist() for k, v in self.variances.items()}
        })
        
        return base_dict
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BayesianScorer':
        """Load from dictionary."""
        scorer = cls(
            name=config['name'],
            use_log_prob=config['use_log_prob'],
            prior_strength=config['prior_strength'],
            min_variance=config['min_variance']
        )
        
        scorer.is_trained = config['is_trained']
        scorer.metadata = config['metadata']
        scorer.context_dim = config['context_dim']
        scorer.total_observations = config['total_observations']
        scorer.num_candidates = config['num_candidates']
        
        # Restore parameters
        scorer.priors = {eval(k): v for k, v in config['priors'].items()}
        scorer.means = {eval(k): np.array(v) for k, v in config['means'].items()}
        scorer.variances = {eval(k): np.array(v) for k, v in config['variances'].items()}
        
        return scorer
