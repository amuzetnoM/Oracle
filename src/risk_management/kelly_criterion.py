"""
Kelly Criterion Position Sizing

Implements the Kelly criterion for optimal position sizing based on
edge (expected return) and odds (win probability).
"""

import numpy as np
from typing import Optional, Union


class KellyCriterion:
    """
    Calculate optimal position size using the Kelly criterion.
    
    The Kelly formula determines what fraction of capital to risk to
    maximize long-term growth rate.
    """
    
    def __init__(self, max_fraction: float = 1.0, fractional_kelly: float = 1.0):
        """
        Initialize Kelly criterion calculator.
        
        Args:
            max_fraction: Maximum fraction of capital to risk (cap)
            fractional_kelly: Fraction of full Kelly to use (e.g., 0.5 for half-Kelly)
        """
        if not 0 < max_fraction <= 1:
            raise ValueError("max_fraction must be between 0 and 1")
        if not 0 < fractional_kelly <= 1:
            raise ValueError("fractional_kelly must be between 0 and 1")
        
        self.max_fraction = max_fraction
        self.fractional_kelly = fractional_kelly
    
    def calculate_simple(
        self,
        win_probability: float,
        win_loss_ratio: float
    ) -> float:
        """
        Calculate Kelly fraction using simple win/loss formulation.
        
        Kelly% = (p * b - q) / b
        where:
            p = probability of winning
            q = probability of losing = 1 - p
            b = win/loss ratio (how much you win vs. how much you lose)
        
        Args:
            win_probability: Probability of winning (0 to 1)
            win_loss_ratio: Ratio of win amount to loss amount
        
        Returns:
            Optimal fraction of capital to risk
        """
        if not 0 <= win_probability <= 1:
            raise ValueError("win_probability must be between 0 and 1")
        if win_loss_ratio <= 0:
            raise ValueError("win_loss_ratio must be positive")
        
        loss_probability = 1 - win_probability
        
        # Kelly formula
        kelly_fraction = (win_probability * win_loss_ratio - loss_probability) / win_loss_ratio
        
        # Apply fractional Kelly and cap
        kelly_fraction = kelly_fraction * self.fractional_kelly
        kelly_fraction = max(0, min(kelly_fraction, self.max_fraction))
        
        return kelly_fraction
    
    def calculate_continuous(
        self,
        expected_return: float,
        variance: float
    ) -> float:
        """
        Calculate Kelly fraction for continuous returns.
        
        Kelly% = μ / σ²
        where:
            μ = expected return
            σ² = variance of returns
        
        Args:
            expected_return: Expected return (mean)
            variance: Variance of returns
        
        Returns:
            Optimal fraction of capital to risk
        """
        if variance <= 0:
            raise ValueError("variance must be positive")
        
        # Kelly formula for continuous case
        kelly_fraction = expected_return / variance
        
        # Apply fractional Kelly and cap
        kelly_fraction = kelly_fraction * self.fractional_kelly
        kelly_fraction = max(0, min(kelly_fraction, self.max_fraction))
        
        return kelly_fraction
    
    def calculate_from_returns(
        self,
        returns: np.ndarray
    ) -> float:
        """
        Calculate Kelly fraction from historical returns.
        
        Args:
            returns: Array of historical returns
        
        Returns:
            Optimal fraction of capital to risk
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        expected_return = np.mean(returns)
        variance = np.var(returns, ddof=1)
        
        return self.calculate_continuous(expected_return, variance)
    
    def calculate_from_sharpe(
        self,
        sharpe_ratio: float
    ) -> float:
        """
        Calculate Kelly fraction from Sharpe ratio.
        
        Kelly% ≈ Sharpe ratio for small values
        
        Args:
            sharpe_ratio: Sharpe ratio of the strategy
        
        Returns:
            Optimal fraction of capital to risk
        """
        # For small returns, Kelly ≈ Sharpe ratio
        kelly_fraction = sharpe_ratio
        
        # Apply fractional Kelly and cap
        kelly_fraction = kelly_fraction * self.fractional_kelly
        kelly_fraction = max(0, min(kelly_fraction, self.max_fraction))
        
        return kelly_fraction
    
    def calculate_multi_asset(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Calculate optimal Kelly fractions for multiple assets.
        
        Uses mean-variance optimization with Kelly criterion.
        
        Args:
            expected_returns: Array of expected returns for each asset
            covariance_matrix: Covariance matrix of returns
        
        Returns:
            Array of optimal fractions for each asset
        """
        if len(expected_returns) != covariance_matrix.shape[0]:
            raise ValueError("Dimensions mismatch")
        if covariance_matrix.shape[0] != covariance_matrix.shape[1]:
            raise ValueError("Covariance matrix must be square")
        
        # Kelly optimal portfolio weights
        # w* = Σ^(-1) * μ
        try:
            inv_cov = np.linalg.inv(covariance_matrix)
            kelly_weights = inv_cov @ expected_returns
        except np.linalg.LinAlgError:
            # If singular, use pseudo-inverse
            inv_cov = np.linalg.pinv(covariance_matrix)
            kelly_weights = inv_cov @ expected_returns
        
        # Apply fractional Kelly
        kelly_weights = kelly_weights * self.fractional_kelly
        
        # Normalize if sum exceeds max_fraction
        total = np.sum(np.abs(kelly_weights))
        if total > self.max_fraction:
            kelly_weights = kelly_weights * (self.max_fraction / total)
        
        return kelly_weights
    
    def expected_growth_rate(
        self,
        win_probability: float,
        win_loss_ratio: float,
        fraction: Optional[float] = None
    ) -> float:
        """
        Calculate expected growth rate for a given position size.
        
        Args:
            win_probability: Probability of winning
            win_loss_ratio: Ratio of win amount to loss amount
            fraction: Fraction to use (if None, uses Kelly optimal)
        
        Returns:
            Expected logarithmic growth rate
        """
        if fraction is None:
            fraction = self.calculate_simple(win_probability, win_loss_ratio)
        
        loss_probability = 1 - win_probability
        
        # Expected log growth rate
        # E[log(1 + f*X)] = p*log(1 + f*b) + q*log(1 - f)
        if fraction >= 1 / win_loss_ratio:
            # Fraction too large - risk of ruin
            return -np.inf
        
        growth_rate = (
            win_probability * np.log(1 + fraction * win_loss_ratio) +
            loss_probability * np.log(1 - fraction)
        )
        
        return growth_rate
    
    def risk_of_ruin(
        self,
        win_probability: float,
        win_loss_ratio: float,
        fraction: float,
        num_bets: int = 100
    ) -> float:
        """
        Estimate probability of losing a significant fraction of capital.
        
        Args:
            win_probability: Probability of winning
            win_loss_ratio: Ratio of win amount to loss amount
            fraction: Fraction of capital risked per bet
            num_bets: Number of bets to simulate
        
        Returns:
            Estimated probability of 50%+ drawdown
        """
        # Simple approximation using binomial distribution
        from scipy import stats
        
        # Calculate break-even number of wins
        # Need enough wins to overcome losses
        min_wins_needed = int(np.ceil(num_bets / (1 + win_loss_ratio)))
        
        # Probability of getting fewer than needed wins
        risk = stats.binom.cdf(min_wins_needed - 1, num_bets, win_probability)
        
        return risk
