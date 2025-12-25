"""
Conditional Value at Risk (CVaR) Calculator

Also known as Expected Shortfall (ES), CVaR measures the expected loss
given that the loss exceeds the VaR threshold.
"""

import numpy as np
from typing import Optional


class CVaRCalculator:
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
    
    CVaR answers: "What is the average loss in the worst X% of scenarios?"
    It provides a more comprehensive risk measure than VaR.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize CVaR calculator.
        
        Args:
            confidence_level: Confidence level for CVaR (e.g., 0.95 for 95%)
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
        Calculate CVaR using historical simulation method.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
        
        Returns:
            CVaR value (expected loss in worst scenarios)
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        # Sort returns in ascending order (worst losses first)
        sorted_returns = np.sort(returns)
        
        # Find the cutoff index for the confidence level
        # For 95% confidence, we look at the worst 5% of returns
        cutoff_index = int(np.ceil(len(sorted_returns) * (1 - self.confidence_level)))
        
        # Ensure at least one observation
        cutoff_index = max(1, cutoff_index)
        
        # Calculate the average of the worst returns
        worst_returns = sorted_returns[:cutoff_index]
        cvar_return = np.mean(worst_returns)
        
        # Convert to CVaR (positive number representing loss)
        cvar = -cvar_return * portfolio_value
        
        return cvar
    
    def calculate_parametric(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0
    ) -> float:
        """
        Calculate CVaR using parametric method.
        Assumes returns are normally distributed.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
        
        Returns:
            CVaR value (expected loss in worst scenarios)
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        from scipy import stats
        
        # Calculate mean and standard deviation
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        # For normal distribution, CVaR can be calculated analytically
        # CVaR = μ - σ * φ(Φ^(-1)(α)) / α
        # where α = 1 - confidence_level
        alpha = 1 - self.confidence_level
        z_score = stats.norm.ppf(alpha)
        
        # Calculate CVaR return
        # CVaR = mean - std * pdf(z) / alpha
        pdf_at_z = stats.norm.pdf(z_score)
        cvar_return = mean_return - std_return * pdf_at_z / alpha
        
        # Convert to CVaR (positive number representing loss)
        cvar = -cvar_return * portfolio_value
        
        return cvar
    
    def calculate(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0,
        method: str = 'historical'
    ) -> float:
        """
        Calculate CVaR using specified method.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
            method: Calculation method ('historical' or 'parametric')
        
        Returns:
            CVaR value (expected loss in worst scenarios)
        """
        if method == 'historical':
            return self.calculate_historical(returns, portfolio_value)
        elif method == 'parametric':
            return self.calculate_parametric(returns, portfolio_value)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def calculate_with_var(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0,
        method: str = 'historical'
    ) -> tuple:
        """
        Calculate both VaR and CVaR together.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
            method: Calculation method
        
        Returns:
            Tuple of (VaR, CVaR)
        """
        from .var_calculator import VaRCalculator
        
        var_calc = VaRCalculator(self.confidence_level)
        var = var_calc.calculate(returns, portfolio_value, method)
        cvar = self.calculate(returns, portfolio_value, method)
        
        return var, cvar
    
    def calculate_contribution(
        self,
        returns: np.ndarray,
        asset_returns: np.ndarray,
        portfolio_value: float = 1.0,
        asset_weight: float = 1.0
    ) -> float:
        """
        Calculate asset's contribution to portfolio CVaR.
        
        Args:
            returns: Array of portfolio returns
            asset_returns: Array of individual asset returns
            portfolio_value: Current portfolio value
            asset_weight: Weight of asset in portfolio
        
        Returns:
            Asset's CVaR contribution
        """
        if len(returns) != len(asset_returns):
            raise ValueError("Returns arrays must have the same length")
        
        # Calculate portfolio CVaR
        portfolio_cvar = self.calculate_historical(returns, portfolio_value)
        
        # Find worst scenarios (below VaR threshold)
        sorted_indices = np.argsort(returns)
        cutoff_index = int(np.ceil(len(returns) * (1 - self.confidence_level)))
        worst_indices = sorted_indices[:cutoff_index]
        
        # Calculate average asset return in worst scenarios
        worst_asset_returns = asset_returns[worst_indices]
        avg_worst_asset_return = np.mean(worst_asset_returns)
        
        # CVaR contribution ≈ weight * avg_worst_asset_return / CVaR
        contribution = asset_weight * (-avg_worst_asset_return * portfolio_value)
        
        return contribution
    
    def risk_ratio(
        self,
        returns: np.ndarray,
        portfolio_value: float = 1.0
    ) -> float:
        """
        Calculate the ratio of CVaR to VaR.
        
        A higher ratio indicates fat tails in the loss distribution.
        
        Args:
            returns: Array of historical returns
            portfolio_value: Current portfolio value
        
        Returns:
            CVaR/VaR ratio
        """
        var, cvar = self.calculate_with_var(returns, portfolio_value)
        
        if var == 0:
            return 1.0
        
        return cvar / var
