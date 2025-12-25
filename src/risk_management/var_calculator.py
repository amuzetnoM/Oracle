"""
Value at Risk (VaR) Calculator

Implements VaR calculation using historical simulation and parametric methods.
VaR estimates the potential loss in portfolio value over a given time period
at a specified confidence level.
"""

import numpy as np
from typing import Union, Optional


class VaRCalculator:
    """
    Calculate Value at Risk (VaR) for portfolio or asset returns.
    
    VaR answers: "What is the maximum loss that can occur with X% confidence
    over the next N days?"
    """
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize VaR calculator.
        
        Args:
            confidence_level: Confidence level for VaR (e.g., 0.95 for 95%)
        """
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        self.confidence_level = confidence_level
    
    def calculate_historical(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0
    ) -> float:
        """
        Calculate VaR using historical simulation method.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value (default: 1.0 for percentage)
        
        Returns:
            VaR value (potential loss amount)
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        # Sort returns in ascending order (worst losses first)
        sorted_returns = np.sort(returns)
        
        # Find the return at the confidence level percentile
        # For 95% confidence, we look at the 5th percentile (worst 5%)
        percentile = (1 - self.confidence_level) * 100
        var_return = np.percentile(sorted_returns, percentile)
        
        # Convert to VaR (positive number representing loss)
        var = -var_return * portfolio_value
        
        return var
    
    def calculate_parametric(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0
    ) -> float:
        """
        Calculate VaR using parametric (variance-covariance) method.
        Assumes returns are normally distributed.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
        
        Returns:
            VaR value (potential loss amount)
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        # Calculate mean and standard deviation
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        # Calculate z-score for confidence level
        # For 95% confidence: z ≈ 1.645 (one-tailed)
        from scipy import stats
        z_score = stats.norm.ppf(self.confidence_level)
        
        # Calculate VaR
        # VaR = -(mean - z * std) * portfolio_value
        var_return = mean_return - z_score * std_return
        var = -var_return * portfolio_value
        
        return var
    
    def calculate_cornish_fisher(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0
    ) -> float:
        """
        Calculate VaR using Cornish-Fisher expansion.
        Adjusts for skewness and kurtosis in the return distribution.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
        
        Returns:
            VaR value (potential loss amount)
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        from scipy import stats
        
        # Calculate distribution moments
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns, fisher=True)  # Excess kurtosis
        
        # Calculate z-score for confidence level
        z = stats.norm.ppf(self.confidence_level)
        
        # Cornish-Fisher adjustment
        z_cf = (z +
                (z**2 - 1) * skewness / 6 +
                (z**3 - 3*z) * kurtosis / 24 -
                (2*z**3 - 5*z) * skewness**2 / 36)
        
        # Calculate VaR
        var_return = mean_return - z_cf * std_return
        var = -var_return * portfolio_value
        
        return var
    
    def calculate(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0,
        method: str = 'historical'
    ) -> float:
        """
        Calculate VaR using specified method.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
            method: Calculation method ('historical', 'parametric', 'cornish_fisher')
        
        Returns:
            VaR value (potential loss amount)
        """
        if method == 'historical':
            return self.calculate_historical(returns, portfolio_value)
        elif method == 'parametric':
            return self.calculate_parametric(returns, portfolio_value)
        elif method == 'cornish_fisher':
            return self.calculate_cornish_fisher(returns, portfolio_value)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def calculate_marginal_var(
        self,
        returns: np.ndarray,
        asset_returns: np.ndarray,
        portfolio_value: float = 1.0,
        asset_weight: float = 1.0
    ) -> float:
        """
        Calculate marginal VaR - the change in portfolio VaR from a small
        change in position size.
        
        Args:
            returns: Array of portfolio returns
            asset_returns: Array of individual asset returns
            portfolio_value: Current portfolio value
            asset_weight: Weight of asset in portfolio
        
        Returns:
            Marginal VaR value
        """
        if len(returns) != len(asset_returns):
            raise ValueError("Returns arrays must have the same length")
        
        # Calculate portfolio VaR
        portfolio_var = self.calculate_historical(returns, portfolio_value)
        
        # Calculate correlation between asset and portfolio
        correlation = np.corrcoef(asset_returns, returns)[0, 1]
        
        # Calculate asset volatility
        asset_std = np.std(asset_returns, ddof=1)
        
        # Marginal VaR approximation
        # MVaR ≈ VaR * correlation * (asset_std / portfolio_std)
        portfolio_std = np.std(returns, ddof=1)
        
        marginal_var = portfolio_var * correlation * (asset_std / portfolio_std)
        
        return marginal_var
