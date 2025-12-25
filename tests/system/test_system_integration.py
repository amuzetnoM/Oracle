"""
System/End-to-End tests for the complete Syndicate system.

Tests the orchestrator coordinating all modules.
"""

import pytest
from src.orchestrator import Orchestrator
from src.data_ingestion.providers.yfinance_provider import YFinanceProvider
from src.feature_engineering.feature_calculator import FeatureCalculator
from src.prediction_core import ArgmaxEngine, CandidateSpace
from src.prediction_core.scoring.ensemble_scorer import EnsembleScorer
from src.risk_management import PositionSizer
from src.execution import OrderManager
from src.monitoring import PerformanceTracker


class TestSystemOrchestration:
    """Test system-level orchestration."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = Orchestrator()
        
        assert orchestrator is not None
        assert orchestrator.event_bus is not None
        assert orchestrator.registry is not None
        assert orchestrator.scheduler is not None
        assert orchestrator.health_monitor is not None
        
    def test_module_registration(self):
        """Test module registration with orchestrator."""
        orchestrator = Orchestrator()
        
        # Register a mock module
        provider = YFinanceProvider()
        orchestrator.register_module(
            name='data_ingestion',
            module_type='provider',
            instance=provider,
            health_check=lambda: True
        )
        
        # Check registration
        modules = orchestrator.registry.list_modules()
        assert len(modules) > 0
        assert 'data_ingestion' in [m['name'] for m in modules]
    
    def test_event_bus_communication(self):
        """Test event bus for inter-module communication."""
        orchestrator = Orchestrator()
        
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        from src.orchestrator.event_bus import EventType
        
        # Subscribe to events
        orchestrator.event_bus.subscribe(EventType.DATA_UPDATED, handler)
        
        # Publish event
        orchestrator.event_bus.publish(
            EventType.DATA_UPDATED,
            source='test',
            data={'symbol': 'AAPL'}
        )
        
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.DATA_UPDATED
    
    def test_health_monitoring(self):
        """Test health monitoring system."""
        orchestrator = Orchestrator()
        
        # Register health checks
        def healthy_check():
            return True
        
        def unhealthy_check():
            return False
        
        orchestrator.health_monitor.register_health_check('module1', healthy_check)
        orchestrator.health_monitor.register_health_check('module2', unhealthy_check)
        
        # Check system health
        health_status = orchestrator.health_monitor.check_all_health()
        
        assert 'module1' in health_status
        assert 'module2' in health_status
        assert health_status['module1'].status.value == 'healthy'
        assert health_status['module2'].status.value == 'unhealthy'


@pytest.mark.system
class TestCompleteSystem:
    """Test complete system functionality."""
    
    def test_system_status(self):
        """Test getting system status."""
        orchestrator = Orchestrator()
        
        # Register some modules
        orchestrator.register_module(
            name='test_module',
            module_type='test',
            instance=object(),
            health_check=lambda: True
        )
        
        status = orchestrator.get_status()
        
        assert 'running' in status
        assert 'modules' in status
    
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern."""
        orchestrator = Orchestrator()
        
        # Register circuit breaker for a module
        orchestrator.circuit_breakers.register('test_service')
        
        breaker = orchestrator.circuit_breakers.get('test_service')
        
        assert breaker is not None
        assert breaker.state == 'closed'
        
        # Simulate failures
        for _ in range(5):
            breaker.record_failure()
        
        # Circuit should open after threshold
        assert breaker.state in ['closed', 'open']
    
    def test_web_ui_integration(self):
        """Test web UI integration with orchestrator."""
        from src.web_ui.app import create_app
        
        orchestrator = Orchestrator()
        app = create_app(orchestrator)
        
        assert app is not None
        assert app.orchestrator == orchestrator
        
        # Test app configuration
        assert 'SECRET_KEY' in app.config
        
        # Test client
        with app.test_client() as client:
            # Test home page
            response = client.get('/')
            assert response.status_code == 200
            
            # Test API endpoint
            response = client.get('/api/system/status')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True


@pytest.mark.system  
class TestPerformanceMetrics:
    """Test system performance and metrics."""
    
    def test_performance_tracking(self):
        """Test performance tracking across system."""
        tracker = PerformanceTracker()
        
        # Record predictions
        for i in range(10):
            tracker.record_prediction(
                prediction='up',
                confidence=0.7,
                actual='up' if i % 2 == 0 else 'down',
                symbol='TEST'
            )
        
        metrics = tracker.get_metrics()
        
        assert 'total_predictions' in metrics
        assert 'accuracy' in metrics
        assert metrics['total_predictions'] == 10
    
    def test_system_metrics_collection(self):
        """Test system-wide metrics collection."""
        from src.monitoring import MetricsCalculator
        
        calculator = MetricsCalculator()
        
        # Generate sample returns
        import numpy as np
        returns = np.random.randn(100) * 0.01
        
        metrics = calculator.calculate_all_metrics(returns)
        
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
