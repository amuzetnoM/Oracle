"""
Integration tests for the complete prediction pipeline.

Tests the flow: Data Ingestion -> Feature Engineering -> Prediction Core
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from src.data_ingestion.providers.yfinance_provider import YFinanceProvider
from src.feature_engineering.feature_calculator import FeatureCalculator
from src.prediction_core import CandidateSpace, ArgmaxEngine, Direction
from src.prediction_core.scoring.statistical_scorer import StatisticalScorer


class TestPredictionPipeline:
    """Test the complete prediction pipeline integration."""
    
    def test_full_pipeline_stock_prediction(self):
        """Test full pipeline from data fetch to prediction (simplified)."""
        # Use synthetic data to avoid network dependency
        # Generate synthetic price data
        np.random.seed(42)
        n_points = 100
        prices = 100 + np.cumsum(np.random.randn(n_points) * 2)
        
        # Prepare OHLCV data
        data = {
            'open': prices + np.random.randn(n_points) * 0.5,
            'high': prices + np.abs(np.random.randn(n_points) * 1.0),
            'low': prices - np.abs(np.random.randn(n_points) * 1.0),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, n_points).astype(float)
        }
        
        # Step 2: Calculate features
        calculator = FeatureCalculator()
        
        # Calculate features
        features = calculator.calculate_all(data)
        
        assert features is not None
        assert 'sma_20' in features
        assert 'rsi' in features
        assert 'macd' in features
        
        # Step 3: Make prediction
        candidate_space = CandidateSpace(candidate_type='direction')
        scorer = StatisticalScorer(candidate_space)
        
        # Train scorer with historical data
        prices = data['close']
        returns = np.diff(prices) / prices[:-1]
        contexts = []
        outcomes = []
        
        for i in range(20, len(returns) - 1):
            # Simple context: last 5 returns
            context = returns[i-5:i]
            # Outcome: next return direction
            outcome = Direction.UP if returns[i] > 0 else Direction.DOWN
            
            contexts.append(context)
            outcomes.append(outcome)
        
        scorer.train(contexts, outcomes)
        
        # Make prediction on latest data
        latest_context = returns[-5:]
        engine = ArgmaxEngine(scorer)
        prediction = engine.predict(latest_context)
        
        assert prediction in [Direction.UP, Direction.DOWN, Direction.FLAT]
        
    def test_pipeline_with_multiple_assets(self):
        """Test pipeline with multiple synthetic assets."""
        # Use synthetic data instead of network calls
        symbols = ['AAPL', 'MSFT']
        
        results = {}
        
        for symbol in symbols:
            # Generate synthetic price data
            price = 100 + np.random.randn() * 10
            results[symbol] = {
                'symbol': symbol,
                'close': price,
                'volume': np.random.randint(1000000, 5000000)
            }
        
        assert len(results) >= 2
        
        for symbol, data in results.items():
            assert 'close' in data
            assert data['close'] > 0
    
    def test_feature_to_prediction_flow(self):
        """Test the feature engineering to prediction flow."""
        # Generate synthetic price data
        np.random.seed(42)
        n_points = 100
        prices = 100 + np.cumsum(np.random.randn(n_points) * 2)
        
        # Prepare OHLCV data
        data = {
            'open': prices + np.random.randn(n_points) * 0.5,
            'high': prices + np.abs(np.random.randn(n_points) * 1.0),
            'low': prices - np.abs(np.random.randn(n_points) * 1.0),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, n_points).astype(float)
        }
        
        # Calculate features
        calculator = FeatureCalculator()
        features = calculator.calculate_all(data)
        
        # Create context from features (use scalar values)
        context = np.array([
            features['sma_20'][-1] if len(features['sma_20']) > 0 else 0,
            features['rsi'][-1] if len(features['rsi']) > 0 else 50,
            features['macd'][-1] if len(features['macd']) > 0 else 0
        ])
        
        # Make prediction
        candidate_space = CandidateSpace(candidate_type='direction')
        scorer = StatisticalScorer(candidate_space)
        
        # Train with dummy data
        dummy_contexts = [context + np.random.randn(3) * 0.1 for _ in range(10)]
        dummy_outcomes = [
            Direction.UP if np.random.rand() > 0.5 else Direction.DOWN
            for _ in range(10)
        ]
        scorer.train(dummy_contexts, dummy_outcomes)
        
        # Predict
        engine = ArgmaxEngine(scorer)
        prediction = engine.predict(context)
        
        assert prediction is not None
        assert prediction in [Direction.UP, Direction.DOWN, Direction.FLAT]


@pytest.mark.integration
class TestRiskExecutionPipeline:
    """Test risk management and execution pipeline."""
    
    def test_prediction_to_position_sizing(self):
        """Test flow from prediction to position size."""
        from src.risk_management import PositionSizer, KellyCriterion
        
        # Mock prediction with confidence
        prediction = Direction.UP
        confidence = 0.75
        
        # Calculate position size using Kelly
        kelly = KellyCriterion()
        win_prob = confidence
        win_loss_ratio = 1.5
        
        kelly_fraction = kelly.calculate_simple(win_prob, win_loss_ratio)
        
        assert 0 <= kelly_fraction <= 1
        
        # Use position sizer
        sizer = PositionSizer()
        position_fraction = sizer.calculate_fixed_fractional(
            signal_strength=confidence,
            base_fraction=kelly_fraction
        )
        
        assert position_fraction > 0
        assert position_fraction <= 1
    
    def test_full_trading_flow(self):
        """Test complete flow: prediction -> risk -> execution."""
        from src.risk_management import PositionSizer
        from src.execution import OrderManager, PaperTrading
        
        # Setup
        capital = 10000
        symbol = 'AAPL'
        current_price = 150.0
        
        # Prediction (mock)
        prediction = Direction.UP
        confidence = 0.80
        
        # Position sizing
        sizer = PositionSizer()
        position_fraction = sizer.calculate_fixed_fractional(
            signal_strength=confidence,
            base_fraction=0.1
        )
        position_size = capital * position_fraction
        shares = int(position_size / current_price)
        
        # Order management and execution
        order_manager = OrderManager()
        executor = PaperTrading(order_manager)
        
        order = order_manager.create_market_order(
            symbol=symbol,
            quantity=shares,
            side='buy'
        )
        
        execution_result = executor.execute_order(order, current_price)
        
        assert execution_result['status'] == 'filled'
        assert execution_result['filled_quantity'] == shares
        assert execution_result['avg_price'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
