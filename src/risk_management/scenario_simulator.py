"""
Scenario Simulator

Monte Carlo simulation for portfolio risk assessment.
Simulates potential future scenarios based on historical data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SimulationResult:
    """Results from a Monte Carlo simulation."""
    scenarios: np.ndarray  # Array of simulated paths (n_scenarios x n_periods)
    final_values: np.ndarray  # Final values for each scenario
    percentiles: Dict[float, float]  # Percentile values
    mean: float
    std: float
    var_95: float  # VaR at 95% confidence
    cvar_95: float  # CVaR at 95% confidence


class ScenarioSimulator:
    """
    Monte Carlo simulation for portfolio risk assessment.
    
    Simulates future portfolio values based on historical return distributions.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        """
        Initialize scenario simulator.
        
        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def simulate_returns(
        self,
        historical_returns: np.ndarray,
        n_scenarios: int = 10000,
        n_periods: int = 252,
        method: str = 'bootstrap'
    ) -> np.ndarray:
        """
        Simulate future returns based on historical data.
        
        Args:
            historical_returns: Array of historical returns
            n_scenarios: Number of scenarios to simulate
            n_periods: Number of periods to simulate (e.g., 252 for 1 year daily)
            method: Simulation method ('bootstrap', 'parametric', 'geometric')
        
        Returns:
            Array of simulated returns (n_scenarios x n_periods)
        """
        if len(historical_returns) == 0:
            raise ValueError("Historical returns cannot be empty")
        
        if method == 'bootstrap':
            return self._simulate_bootstrap(
                historical_returns, n_scenarios, n_periods
            )
        elif method == 'parametric':
            return self._simulate_parametric(
                historical_returns, n_scenarios, n_periods
            )
        elif method == 'geometric':
            return self._simulate_geometric(
                historical_returns, n_scenarios, n_periods
            )
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _simulate_bootstrap(
        self,
        historical_returns: np.ndarray,
        n_scenarios: int,
        n_periods: int
    ) -> np.ndarray:
        """
        Simulate returns using bootstrap resampling.
        
        Randomly samples from historical returns with replacement.
        """
        simulated = np.random.choice(
            historical_returns,
            size=(n_scenarios, n_periods),
            replace=True
        )
        return simulated
    
    def _simulate_parametric(
        self,
        historical_returns: np.ndarray,
        n_scenarios: int,
        n_periods: int
    ) -> np.ndarray:
        """
        Simulate returns assuming normal distribution.
        
        Uses mean and std of historical returns.
        """
        mean = np.mean(historical_returns)
        std = np.std(historical_returns, ddof=1)
        
        simulated = np.random.normal(
            loc=mean,
            scale=std,
            size=(n_scenarios, n_periods)
        )
        return simulated
    
    def _simulate_geometric(
        self,
        historical_returns: np.ndarray,
        n_scenarios: int,
        n_periods: int
    ) -> np.ndarray:
        """
        Simulate returns using geometric Brownian motion.
        
        Commonly used for asset price modeling.
        """
        # Convert returns to log returns
        log_returns = np.log(1 + historical_returns)
        
        # Calculate parameters
        mu = np.mean(log_returns)
        sigma = np.std(log_returns, ddof=1)
        
        # Adjust for discrete time
        drift = mu - 0.5 * sigma ** 2
        
        # Simulate
        random_shocks = np.random.normal(0, 1, size=(n_scenarios, n_periods))
        log_returns_sim = drift + sigma * random_shocks
        
        # Convert back to simple returns
        simulated = np.exp(log_returns_sim) - 1
        
        return simulated
    
    def simulate_portfolio_value(
        self,
        initial_value: float,
        historical_returns: np.ndarray,
        n_scenarios: int = 10000,
        n_periods: int = 252,
        method: str = 'bootstrap'
    ) -> SimulationResult:
        """
        Simulate future portfolio values.
        
        Args:
            initial_value: Starting portfolio value
            historical_returns: Array of historical returns
            n_scenarios: Number of scenarios to simulate
            n_periods: Number of periods to simulate
            method: Simulation method
        
        Returns:
            SimulationResult with paths and statistics
        """
        # Simulate returns
        simulated_returns = self.simulate_returns(
            historical_returns, n_scenarios, n_periods, method
        )
        
        # Convert returns to value paths
        # Value(t) = Value(0) * prod(1 + r_i)
        cumulative_returns = np.cumprod(1 + simulated_returns, axis=1)
        scenarios = initial_value * cumulative_returns
        
        # Final values
        final_values = scenarios[:, -1]
        
        # Calculate statistics
        mean = np.mean(final_values)
        std = np.std(final_values, ddof=1)
        
        # Calculate percentiles
        percentiles = {
            0.01: np.percentile(final_values, 1),
            0.05: np.percentile(final_values, 5),
            0.10: np.percentile(final_values, 10),
            0.25: np.percentile(final_values, 25),
            0.50: np.percentile(final_values, 50),
            0.75: np.percentile(final_values, 75),
            0.90: np.percentile(final_values, 90),
            0.95: np.percentile(final_values, 95),
            0.99: np.percentile(final_values, 99),
        }
        
        # Calculate VaR and CVaR (as losses)
        losses = initial_value - final_values
        var_95 = np.percentile(losses, 95)
        
        # CVaR: average of losses exceeding VaR
        worst_losses = losses[losses >= var_95]
        cvar_95 = np.mean(worst_losses) if len(worst_losses) > 0 else var_95
        
        return SimulationResult(
            scenarios=scenarios,
            final_values=final_values,
            percentiles=percentiles,
            mean=mean,
            std=std,
            var_95=var_95,
            cvar_95=cvar_95
        )
    
    def simulate_with_position_sizing(
        self,
        initial_value: float,
        historical_returns: np.ndarray,
        position_size: float,
        n_scenarios: int = 10000,
        n_periods: int = 252
    ) -> SimulationResult:
        """
        Simulate portfolio with specific position sizing.
        
        Args:
            initial_value: Starting portfolio value
            historical_returns: Historical returns of the asset
            position_size: Fraction of capital allocated (0-1)
            n_scenarios: Number of scenarios
            n_periods: Number of periods
        
        Returns:
            SimulationResult with scaled returns
        """
        # Scale returns by position size
        scaled_returns = historical_returns * position_size
        
        return self.simulate_portfolio_value(
            initial_value,
            scaled_returns,
            n_scenarios,
            n_periods
        )
    
    def stress_test(
        self,
        initial_value: float,
        historical_returns: np.ndarray,
        stress_scenarios: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Run stress tests with specific scenarios.
        
        Args:
            initial_value: Starting portfolio value
            historical_returns: Historical returns
            stress_scenarios: Dict of scenario_name -> return_change
                Example: {'market_crash': -0.30, 'moderate_drop': -0.10}
        
        Returns:
            Dict mapping scenario to final portfolio value
        """
        results = {}
        
        # Add current best estimate
        results['baseline'] = initial_value * (1 + np.mean(historical_returns))
        
        # Test each stress scenario
        for scenario_name, stress_return in stress_scenarios.items():
            final_value = initial_value * (1 + stress_return)
            results[scenario_name] = final_value
        
        return results
    
    def probability_of_profit(
        self,
        initial_value: float,
        historical_returns: np.ndarray,
        n_scenarios: int = 10000,
        n_periods: int = 252
    ) -> float:
        """
        Calculate probability of making a profit.
        
        Args:
            initial_value: Starting portfolio value
            historical_returns: Historical returns
            n_scenarios: Number of scenarios
            n_periods: Number of periods
        
        Returns:
            Probability of profit (0-1)
        """
        result = self.simulate_portfolio_value(
            initial_value,
            historical_returns,
            n_scenarios,
            n_periods
        )
        
        # Count scenarios where final value > initial value
        profitable = np.sum(result.final_values > initial_value)
        probability = profitable / n_scenarios
        
        return probability
    
    def probability_of_ruin(
        self,
        initial_value: float,
        historical_returns: np.ndarray,
        ruin_threshold: float = 0.5,
        n_scenarios: int = 10000,
        n_periods: int = 252
    ) -> float:
        """
        Calculate probability of losing more than threshold.
        
        Args:
            initial_value: Starting portfolio value
            historical_returns: Historical returns
            ruin_threshold: Fraction of capital that constitutes "ruin" (e.g., 0.5)
            n_scenarios: Number of scenarios
            n_periods: Number of periods
        
        Returns:
            Probability of ruin (0-1)
        """
        result = self.simulate_portfolio_value(
            initial_value,
            historical_returns,
            n_scenarios,
            n_periods
        )
        
        ruin_value = initial_value * (1 - ruin_threshold)
        ruined = np.sum(result.final_values < ruin_value)
        probability = ruined / n_scenarios
        
        return probability
    
    def expected_shortfall_time(
        self,
        initial_value: float,
        historical_returns: np.ndarray,
        threshold_value: float,
        n_scenarios: int = 10000,
        n_periods: int = 252
    ) -> float:
        """
        Calculate expected time until portfolio falls below threshold.
        
        Args:
            initial_value: Starting portfolio value
            historical_returns: Historical returns
            threshold_value: Value threshold
            n_scenarios: Number of scenarios
            n_periods: Number of periods
        
        Returns:
            Average time (in periods) until threshold breach
        """
        simulated_returns = self.simulate_returns(
            historical_returns, n_scenarios, n_periods
        )
        
        cumulative_returns = np.cumprod(1 + simulated_returns, axis=1)
        scenarios = initial_value * cumulative_returns
        
        # Find first time each scenario crosses threshold
        breach_times = []
        for scenario in scenarios:
            breach = np.where(scenario < threshold_value)[0]
            if len(breach) > 0:
                breach_times.append(breach[0])
            else:
                breach_times.append(n_periods)  # Never breached
        
        return np.mean(breach_times)
