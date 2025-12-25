"""
Unit tests for risk management module components.
"""

import numpy as np
import pytest
from datetime import datetime

from src.risk_management import (
    VaRCalculator,
    CVaRCalculator,
    KellyCriterion,
    PositionSizer,
    PortfolioTracker,
    ScenarioSimulator
)


class TestVaRCalculator:
    """Tests for VaR calculator."""
    
    def test_initialization(self):
        """Test VaR calculator initialization."""
        calc = VaRCalculator(confidence_level=0.95)
        assert calc.confidence_level == 0.95
    
    def test_invalid_confidence_level(self):
        """Test that invalid confidence level raises error."""
        with pytest.raises(ValueError):
            VaRCalculator(confidence_level=1.5)
    
    def test_historical_var(self):
        """Test historical VaR calculation."""
        # Create sample returns with known distribution
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)
        
        calc = VaRCalculator(confidence_level=0.95)
        var = calc.calculate_historical(returns, portfolio_value=100000)
        
        # VaR should be positive and reasonable
        assert var > 0
        assert var < 100000  # Should not exceed portfolio value
    
    def test_parametric_var(self):
        """Test parametric VaR calculation."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)
        
        calc = VaRCalculator(confidence_level=0.95)
        var = calc.calculate_parametric(returns, portfolio_value=100000)
        
        assert var > 0
        assert var < 100000


class TestCVaRCalculator:
    """Tests for CVaR calculator."""
    
    def test_initialization(self):
        """Test CVaR calculator initialization."""
        calc = CVaRCalculator(confidence_level=0.95)
        assert calc.confidence_level == 0.95
    
    def test_historical_cvar(self):
        """Test historical CVaR calculation."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)
        
        calc = CVaRCalculator(confidence_level=0.95)
        cvar = calc.calculate_historical(returns, portfolio_value=100000)
        
        # CVaR should be positive
        assert cvar > 0
        assert cvar < 100000
    
    def test_cvar_greater_than_var(self):
        """Test that CVaR >= VaR (by definition)."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)
        
        calc = CVaRCalculator(confidence_level=0.95)
        var, cvar = calc.calculate_with_var(returns, portfolio_value=100000)
        
        # CVaR should be greater than or equal to VaR
        assert cvar >= var


class TestKellyCriterion:
    """Tests for Kelly criterion."""
    
    def test_initialization(self):
        """Test Kelly criterion initialization."""
        kelly = KellyCriterion(max_fraction=0.5, fractional_kelly=0.5)
        assert kelly.max_fraction == 0.5
        assert kelly.fractional_kelly == 0.5
    
    def test_simple_kelly(self):
        """Test simple Kelly calculation."""
        kelly = KellyCriterion()
        
        # Fair coin flip with 2:1 payout
        # Kelly = (0.5 * 2 - 0.5) / 2 = 0.25
        fraction = kelly.calculate_simple(
            win_probability=0.5,
            win_loss_ratio=2.0
        )
        
        assert 0 <= fraction <= 1
        assert abs(fraction - 0.25) < 0.01
    
    def test_kelly_zero_for_fair_game(self):
        """Test that Kelly is zero for fair game (no edge)."""
        kelly = KellyCriterion()
        
        # Fair coin flip with 1:1 payout (no edge)
        fraction = kelly.calculate_simple(
            win_probability=0.5,
            win_loss_ratio=1.0
        )
        
        assert fraction == 0
    
    def test_kelly_from_returns(self):
        """Test Kelly calculation from historical returns."""
        np.random.seed(42)
        returns = np.random.normal(0.02, 0.1, 1000)
        
        kelly = KellyCriterion()
        fraction = kelly.calculate_from_returns(returns)
        
        assert 0 <= fraction <= 1


class TestPositionSizer:
    """Tests for position sizer."""
    
    def test_initialization(self):
        """Test position sizer initialization."""
        sizer = PositionSizer(
            max_position_size=0.2,
            max_portfolio_risk=0.02
        )
        assert sizer.max_position_size == 0.2
        assert sizer.max_portfolio_risk == 0.02
    
    def test_fixed_fractional(self):
        """Test fixed fractional position sizing."""
        sizer = PositionSizer()
        
        size = sizer.calculate_fixed_fractional(
            signal_strength=0.8,
            base_fraction=0.02
        )
        
        assert 0 <= size <= sizer.max_position_size
        assert size == 0.02 * 0.8
    
    def test_kelly_based(self):
        """Test Kelly-based position sizing."""
        sizer = PositionSizer()
        
        size = sizer.calculate_kelly_based(
            win_probability=0.6,
            win_loss_ratio=2.0
        )
        
        assert 0 <= size <= 1
    
    def test_from_prediction(self):
        """Test position sizing from prediction."""
        np.random.seed(42)
        historical_returns = np.random.normal(0.001, 0.02, 1000)
        
        sizer = PositionSizer()
        size = sizer.calculate_from_prediction(
            predicted_return=0.05,
            confidence=0.8,
            historical_returns=historical_returns
        )
        
        assert 0 <= size <= 1


class TestPortfolioTracker:
    """Tests for portfolio tracker."""
    
    def test_initialization(self):
        """Test portfolio tracker initialization."""
        tracker = PortfolioTracker(initial_capital=100000)
        assert tracker.initial_capital == 100000
        assert tracker.cash == 100000
        assert len(tracker.positions) == 0
    
    def test_add_position(self):
        """Test adding a position."""
        tracker = PortfolioTracker(initial_capital=100000)
        
        success = tracker.add_position(
            asset='AAPL',
            quantity=100,
            price=150.0
        )
        
        assert success
        assert 'AAPL' in tracker.positions
        assert tracker.positions['AAPL'].quantity == 100
        assert tracker.cash == 100000 - 15000
    
    def test_close_position(self):
        """Test closing a position."""
        tracker = PortfolioTracker(initial_capital=100000)
        
        tracker.add_position('AAPL', 100, 150.0)
        pnl = tracker.close_position('AAPL', 160.0)
        
        assert pnl == 1000  # (160 - 150) * 100
        assert 'AAPL' not in tracker.positions
        assert tracker.realized_pnl == 1000
    
    def test_portfolio_value(self):
        """Test portfolio value calculation."""
        tracker = PortfolioTracker(initial_capital=100000)
        
        tracker.add_position('AAPL', 100, 150.0)
        tracker.update_prices({'AAPL': 160.0})
        
        value = tracker.get_portfolio_value()
        # Cash (85000) + Position value (100 * 160)
        assert value == 85000 + 16000
    
    def test_win_rate(self):
        """Test win rate calculation."""
        tracker = PortfolioTracker(initial_capital=100000)
        
        # Win
        tracker.add_position('AAPL', 100, 150.0)
        tracker.close_position('AAPL', 160.0)
        
        # Loss
        tracker.add_position('MSFT', 100, 200.0)
        tracker.close_position('MSFT', 190.0)
        
        # Win
        tracker.add_position('GOOGL', 100, 100.0)
        tracker.close_position('GOOGL', 110.0)
        
        assert tracker.total_trades == 3
        assert tracker.winning_trades == 2
        assert tracker.losing_trades == 1
        assert tracker.get_win_rate() == pytest.approx(66.67, rel=0.1)


class TestScenarioSimulator:
    """Tests for scenario simulator."""
    
    def test_initialization(self):
        """Test scenario simulator initialization."""
        sim = ScenarioSimulator(random_seed=42)
        assert sim.random_seed == 42
    
    def test_simulate_returns_bootstrap(self):
        """Test bootstrap return simulation."""
        np.random.seed(42)
        historical_returns = np.random.normal(0.001, 0.02, 100)
        
        sim = ScenarioSimulator(random_seed=42)
        simulated = sim.simulate_returns(
            historical_returns,
            n_scenarios=1000,
            n_periods=252,
            method='bootstrap'
        )
        
        assert simulated.shape == (1000, 252)
    
    def test_simulate_returns_parametric(self):
        """Test parametric return simulation."""
        np.random.seed(42)
        historical_returns = np.random.normal(0.001, 0.02, 100)
        
        sim = ScenarioSimulator(random_seed=42)
        simulated = sim.simulate_returns(
            historical_returns,
            n_scenarios=1000,
            n_periods=252,
            method='parametric'
        )
        
        assert simulated.shape == (1000, 252)
    
    def test_simulate_portfolio_value(self):
        """Test portfolio value simulation."""
        np.random.seed(42)
        historical_returns = np.random.normal(0.001, 0.02, 100)
        
        sim = ScenarioSimulator(random_seed=42)
        result = sim.simulate_portfolio_value(
            initial_value=100000,
            historical_returns=historical_returns,
            n_scenarios=1000,
            n_periods=252
        )
        
        assert result.scenarios.shape == (1000, 252)
        assert len(result.final_values) == 1000
        assert result.mean > 0
        assert result.std > 0
        assert result.var_95 >= 0
        assert result.cvar_95 >= result.var_95
    
    def test_probability_of_profit(self):
        """Test probability of profit calculation."""
        np.random.seed(42)
        # Positive expected returns
        historical_returns = np.random.normal(0.01, 0.02, 100)
        
        sim = ScenarioSimulator(random_seed=42)
        prob = sim.probability_of_profit(
            initial_value=100000,
            historical_returns=historical_returns,
            n_scenarios=1000,
            n_periods=252
        )
        
        assert 0 <= prob <= 1
        # With positive expected return, should have >50% probability of profit
        assert prob > 0.5
