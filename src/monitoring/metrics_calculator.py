"""
Metrics Calculator

Calculate trading and portfolio performance metrics.
"""

import numpy as np
from typing import List, Optional


class MetricsCalculator:
    """
    Calculate performance metrics for trading strategies.
    
    Implements Sharpe ratio, Calmar ratio, Sortino ratio, and other metrics.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def sharpe_ratio(
        self,
        returns: np.ndarray,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Sharpe = (Mean Return - Risk Free Rate) / Std Dev
        
        Args:
            returns: Array of returns
            periods_per_year: Number of periods per year (252 for daily)
        
        Returns:
            Annualized Sharpe ratio
        """
        if len(returns) == 0:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Annualize
        excess_return = mean_return - (self.risk_free_rate / periods_per_year)
        sharpe = excess_return / std_return
        sharpe_annual = sharpe * np.sqrt(periods_per_year)
        
        return sharpe_annual
    
    def sortino_ratio(
        self,
        returns: np.ndarray,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino ratio.
        
        Like Sharpe but only considers downside deviation.
        
        Args:
            returns: Array of returns
            periods_per_year: Number of periods per year
        
        Returns:
            Annualized Sortino ratio
        """
        if len(returns) == 0:
            return 0.0
        
        mean_return = np.mean(returns)
        
        # Downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if mean_return > 0 else 0.0
        
        downside_std = np.std(downside_returns, ddof=1)
        
        if downside_std == 0:
            return 0.0
        
        # Annualize
        excess_return = mean_return - (self.risk_free_rate / periods_per_year)
        sortino = excess_return / downside_std
        sortino_annual = sortino * np.sqrt(periods_per_year)
        
        return sortino_annual
    
    def calmar_ratio(
        self,
        returns: np.ndarray,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Calmar ratio.
        
        Calmar = Annualized Return / Maximum Drawdown
        
        Args:
            returns: Array of returns
            periods_per_year: Number of periods per year
        
        Returns:
            Calmar ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Annualized return
        total_return = np.prod(1 + returns) - 1
        periods = len(returns)
        annual_return = (1 + total_return) ** (periods_per_year / periods) - 1
        
        # Maximum drawdown
        max_dd = self.max_drawdown(returns)
        
        if max_dd == 0:
            return float('inf') if annual_return > 0 else 0.0
        
        return annual_return / max_dd
    
    def max_drawdown(self, returns: np.ndarray) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            returns: Array of returns
        
        Returns:
            Maximum drawdown as decimal (e.g., 0.15 for 15%)
        """
        if len(returns) == 0:
            return 0.0
        
        # Calculate cumulative returns
        cumulative = np.cumprod(1 + returns)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(cumulative)
        
        # Calculate drawdown at each point
        drawdowns = (cumulative - running_max) / running_max
        
        return abs(np.min(drawdowns))
    
    def information_ratio(
        self,
        returns: np.ndarray,
        benchmark_returns: np.ndarray,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Information ratio.
        
        IR = (Return - Benchmark Return) / Tracking Error
        
        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns
            periods_per_year: Number of periods per year
        
        Returns:
            Annualized Information ratio
        """
        if len(returns) != len(benchmark_returns):
            raise ValueError("Returns arrays must have same length")
        
        if len(returns) == 0:
            return 0.0
        
        # Active returns
        active_returns = returns - benchmark_returns
        
        mean_active = np.mean(active_returns)
        tracking_error = np.std(active_returns, ddof=1)
        
        if tracking_error == 0:
            return 0.0
        
        ir = mean_active / tracking_error
        ir_annual = ir * np.sqrt(periods_per_year)
        
        return ir_annual
    
    def omega_ratio(
        self,
        returns: np.ndarray,
        threshold: float = 0.0
    ) -> float:
        """
        Calculate Omega ratio.
        
        Omega = Probability-weighted gains / Probability-weighted losses
        
        Args:
            returns: Array of returns
            threshold: Threshold return (typically 0)
        
        Returns:
            Omega ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Returns above threshold
        gains = np.sum(np.maximum(returns - threshold, 0))
        
        # Returns below threshold
        losses = np.sum(np.maximum(threshold - returns, 0))
        
        if losses == 0:
            return float('inf') if gains > 0 else 0.0
        
        return gains / losses
    
    def value_at_risk(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk.
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level (e.g., 0.95)
        
        Returns:
            VaR (as positive number)
        """
        if len(returns) == 0:
            return 0.0
        
        percentile = (1 - confidence_level) * 100
        var = np.percentile(returns, percentile)
        
        return abs(var)
    
    def conditional_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level
        
        Returns:
            CVaR (as positive number)
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.value_at_risk(returns, confidence_level)
        
        # Average of returns worse than VaR
        worst_returns = returns[returns <= -var]
        
        if len(worst_returns) == 0:
            return var
        
        cvar = abs(np.mean(worst_returns))
        
        return cvar
    
    def calculate_all_metrics(
        self,
        returns: np.ndarray,
        benchmark_returns: Optional[np.ndarray] = None,
        periods_per_year: int = 252
    ) -> dict:
        """
        Calculate all available metrics.
        
        Args:
            returns: Strategy returns
            benchmark_returns: Optional benchmark returns
            periods_per_year: Number of periods per year
        
        Returns:
            Dictionary with all metrics
        """
        if len(returns) == 0:
            return {}
        
        metrics = {
            'total_return': float(np.prod(1 + returns) - 1),
            'mean_return': float(np.mean(returns)),
            'std_return': float(np.std(returns, ddof=1)),
            'sharpe_ratio': self.sharpe_ratio(returns, periods_per_year),
            'sortino_ratio': self.sortino_ratio(returns, periods_per_year),
            'calmar_ratio': self.calmar_ratio(returns, periods_per_year),
            'max_drawdown': self.max_drawdown(returns),
            'omega_ratio': self.omega_ratio(returns),
            'var_95': self.value_at_risk(returns, 0.95),
            'cvar_95': self.conditional_var(returns, 0.95),
        }
        
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            metrics['information_ratio'] = self.information_ratio(
                returns, benchmark_returns, periods_per_year
            )
        
        return metrics
