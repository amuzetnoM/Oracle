"""
Position Sizer

Combines risk metrics (VaR, CVaR) with Kelly criterion to determine
optimal position sizes that balance risk and return.
"""

import numpy as np
from typing import Dict, Optional, Union
from .var_calculator import VaRCalculator
from .cvar_calculator import CVaRCalculator
from .kelly_criterion import KellyCriterion


class PositionSizer:
    """
    Calculate position sizes based on risk management rules.
    
    Combines multiple risk measures to determine safe and optimal
    position sizes for trading signals.
    """
    
    def __init__(
        self,
        max_position_size: float = 1.0,
        max_portfolio_risk: float = 0.02,
        confidence_level: float = 0.95,
        fractional_kelly: float = 0.5
    ):
        """
        Initialize position sizer.
        
        Args:
            max_position_size: Maximum fraction of capital per position (0-1)
            max_portfolio_risk: Maximum portfolio risk as fraction of capital
            confidence_level: Confidence level for VaR/CVaR calculations
            fractional_kelly: Fraction of full Kelly to use (default: 0.5 for half-Kelly)
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.confidence_level = confidence_level
        
        self.var_calculator = VaRCalculator(confidence_level)
        self.cvar_calculator = CVaRCalculator(confidence_level)
        self.kelly = KellyCriterion(
            max_fraction=max_position_size,
            fractional_kelly=fractional_kelly
        )
    
    def calculate_fixed_fractional(
        self,
        signal_strength: float,
        base_fraction: float = 0.02
    ) -> float:
        """
        Calculate position size using fixed fractional method.
        
        Args:
            signal_strength: Strength of trading signal (0-1)
            base_fraction: Base fraction to risk
        
        Returns:
            Position size as fraction of capital
        """
        if not 0 <= signal_strength <= 1:
            raise ValueError("signal_strength must be between 0 and 1")
        
        position_size = base_fraction * signal_strength
        position_size = min(position_size, self.max_position_size)
        
        return position_size
    
    def calculate_var_based(
        self,
        returns: np.ndarray,
        portfolio_value: float,
        target_var: float
    ) -> float:
        """
        Calculate position size to achieve target VaR.
        
        Args:
            returns: Historical returns of asset
            portfolio_value: Current portfolio value
            target_var: Target VaR in dollar terms
        
        Returns:
            Position size as fraction of capital
        """
        if len(returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        # Calculate VaR for full position
        full_var = self.var_calculator.calculate_historical(
            returns,
            portfolio_value
        )
        
        if full_var == 0:
            return 0.0
        
        # Scale position to achieve target VaR
        position_size = target_var / full_var
        position_size = min(position_size, self.max_position_size)
        
        return position_size
    
    def calculate_kelly_based(
        self,
        win_probability: float,
        win_loss_ratio: float
    ) -> float:
        """
        Calculate position size using Kelly criterion.
        
        Args:
            win_probability: Probability of winning trade
            win_loss_ratio: Average win / average loss ratio
        
        Returns:
            Position size as fraction of capital
        """
        return self.kelly.calculate_simple(win_probability, win_loss_ratio)
    
    def calculate_from_prediction(
        self,
        predicted_return: float,
        confidence: float,
        historical_returns: np.ndarray
    ) -> float:
        """
        Calculate position size from prediction with confidence.
        
        Combines predicted return, confidence level, and historical
        volatility to determine appropriate position size.
        
        Args:
            predicted_return: Predicted return (e.g., 0.02 for 2%)
            confidence: Confidence in prediction (0-1)
            historical_returns: Historical returns for volatility estimation
        
        Returns:
            Position size as fraction of capital
        """
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if len(historical_returns) == 0:
            raise ValueError("Returns array cannot be empty")
        
        # Estimate variance from historical returns
        variance = np.var(historical_returns, ddof=1)
        
        # Adjust predicted return by confidence
        adjusted_return = predicted_return * confidence
        
        # Use Kelly criterion for continuous case
        if variance > 0:
            kelly_size = self.kelly.calculate_continuous(adjusted_return, variance)
        else:
            kelly_size = 0.0
        
        return kelly_size
    
    def calculate_optimal(
        self,
        predicted_return: float,
        confidence: float,
        historical_returns: np.ndarray,
        portfolio_value: float
    ) -> Dict[str, float]:
        """
        Calculate optimal position size using multiple methods.
        
        Returns position sizes from different approaches for comparison.
        
        Args:
            predicted_return: Predicted return
            confidence: Confidence in prediction
            historical_returns: Historical returns
            portfolio_value: Current portfolio value
        
        Returns:
            Dictionary with position sizes from different methods
        """
        results = {}
        
        # Kelly-based size
        results['kelly'] = self.calculate_from_prediction(
            predicted_return,
            confidence,
            historical_returns
        )
        
        # VaR-based size (targeting max portfolio risk)
        target_var = portfolio_value * self.max_portfolio_risk
        results['var_based'] = self.calculate_var_based(
            historical_returns,
            portfolio_value,
            target_var
        )
        
        # Fixed fractional based on confidence
        results['fixed_fractional'] = self.calculate_fixed_fractional(
            confidence,
            base_fraction=self.max_portfolio_risk
        )
        
        # Conservative: take minimum of all methods
        results['conservative'] = min(
            results['kelly'],
            results['var_based'],
            results['fixed_fractional']
        )
        
        # Balanced: average of methods
        results['balanced'] = np.mean([
            results['kelly'],
            results['var_based'],
            results['fixed_fractional']
        ])
        
        return results
    
    def calculate_multi_position(
        self,
        predictions: Dict[str, Dict],
        portfolio_value: float,
        correlation_matrix: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Calculate position sizes for multiple assets simultaneously.
        
        Takes into account portfolio risk and correlations.
        
        Args:
            predictions: Dict mapping asset to {return, confidence, historical_returns}
            portfolio_value: Current portfolio value
            correlation_matrix: Optional correlation matrix between assets
        
        Returns:
            Dictionary mapping asset to position size (fraction)
        """
        assets = list(predictions.keys())
        n_assets = len(assets)
        
        if n_assets == 0:
            return {}
        
        # Calculate individual position sizes
        individual_sizes = {}
        for asset, pred in predictions.items():
            size = self.calculate_from_prediction(
                pred['predicted_return'],
                pred['confidence'],
                pred['historical_returns']
            )
            individual_sizes[asset] = size
        
        # If no correlation matrix, just scale down if total exceeds limit
        if correlation_matrix is None:
            total_size = sum(individual_sizes.values())
            if total_size > self.max_position_size:
                scale_factor = self.max_position_size / total_size
                return {
                    asset: size * scale_factor
                    for asset, size in individual_sizes.items()
                }
            return individual_sizes
        
        # With correlation matrix, use portfolio variance to adjust
        if correlation_matrix.shape != (n_assets, n_assets):
            raise ValueError("Correlation matrix dimensions don't match number of assets")
        
        # Calculate portfolio variance
        sizes_array = np.array([individual_sizes[asset] for asset in assets])
        
        # Get volatilities
        volatilities = np.array([
            np.std(predictions[asset]['historical_returns'], ddof=1)
            for asset in assets
        ])
        
        # Portfolio variance = w^T * Σ * w
        cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix
        portfolio_var = sizes_array @ cov_matrix @ sizes_array
        
        # Scale down if portfolio risk too high
        target_var = (self.max_portfolio_risk * portfolio_value) ** 2
        if portfolio_var > target_var:
            scale_factor = np.sqrt(target_var / portfolio_var)
            return {
                asset: individual_sizes[asset] * scale_factor
                for asset in assets
            }
        
        return individual_sizes
