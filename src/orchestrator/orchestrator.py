"""
Orchestrator

Main coordination engine that ties all modules together.
"""

from typing import Dict, Optional, Any
import logging

from .event_bus import EventBus, Event, EventType
from .module_registry import ModuleRegistry, ModuleStatus
from .scheduler import Scheduler
from .health_monitor import HealthMonitor, HealthStatus, HealthCheck
from .circuit_breaker import CircuitBreakerRegistry


class Orchestrator:
    """
    Main orchestrator for the Syndicate system.
    
    Coordinates all modules, manages event flow, and ensures system health.
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.event_bus = EventBus()
        self.registry = ModuleRegistry()
        self.scheduler = Scheduler()
        self.health_monitor = HealthMonitor()
        self.circuit_breakers = CircuitBreakerRegistry()
        
        self.running = False
        
        # Setup default event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup default event handlers."""
        # Log all events for debugging
        self.event_bus.subscribe(
            EventType.MODULE_ERROR,
            self._handle_module_error
        )
    
    def _handle_module_error(self, event: Event):
        """Handle module error events."""
        self.logger.error(
            f"Module error from {event.source}: {event.data.get('error', 'Unknown')}"
        )
    
    def register_module(
        self,
        name: str,
        module_type: str,
        instance: Any,
        dependencies: Optional[list] = None,
        health_check: Optional[callable] = None
    ):
        """
        Register a module with the orchestrator.
        
        Args:
            name: Module name
            module_type: Module type
            instance: Module instance
            dependencies: List of dependencies
            health_check: Health check function
        """
        # Register in registry
        self.registry.register(
            name=name,
            module_type=module_type,
            instance=instance,
            dependencies=dependencies or []
        )
        
        # Register health check if provided
        if health_check:
            self.health_monitor.register_health_check(name, health_check)
        
        # Create circuit breaker for module
        self.circuit_breakers.register(name)
        
        self.logger.info(f"Registered module: {name}")
    
    def start(self):
        """Start the orchestrator and all modules."""
        if self.running:
            self.logger.warning("Orchestrator already running")
            return
        
        self.logger.info("Starting orchestrator...")
        
        # Start scheduler
        self.scheduler.start()
        
        # Schedule periodic health checks
        self.scheduler.schedule_every(
            name="health_check",
            callback=self._perform_health_checks,
            minutes=1
        )
        
        # Start modules in dependency order
        startup_order = self.registry.get_startup_order()
        for module_name in startup_order:
            self._start_module(module_name)
        
        self.running = True
        self.logger.info("Orchestrator started")
        
        # Emit system started event
        self.event_bus.emit(
            EventType.MODULE_STARTED,
            source="orchestrator",
            data={'message': 'System started'}
        )
    
    def stop(self):
        """Stop the orchestrator and all modules."""
        if not self.running:
            return
        
        self.logger.info("Stopping orchestrator...")
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Stop all modules
        for module_name in self.registry.list_all():
            self._stop_module(module_name.name)
        
        self.running = False
        self.logger.info("Orchestrator stopped")
        
        # Emit system stopped event
        self.event_bus.emit(
            EventType.MODULE_STOPPED,
            source="orchestrator",
            data={'message': 'System stopped'}
        )
    
    def _start_module(self, module_name: str):
        """Start a specific module."""
        module = self.registry.get(module_name)
        if not module:
            return
        
        try:
            # Check dependencies
            deps = self.registry.check_dependencies(module_name)
            if not all(deps.values()):
                missing = [name for name, satisfied in deps.items() if not satisfied]
                raise Exception(f"Missing dependencies: {missing}")
            
            # Mark as initializing
            self.registry.update_status(module_name, ModuleStatus.INITIALIZING)
            
            # Start module if it has a start method
            if hasattr(module.instance, 'start'):
                module.instance.start()
            
            # Mark as running
            self.registry.update_status(module_name, ModuleStatus.RUNNING)
            
            self.logger.info(f"Started module: {module_name}")
            
            # Emit event
            self.event_bus.emit(
                EventType.MODULE_STARTED,
                source=module_name,
                data={'module': module_name}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start module {module_name}: {e}")
            self.registry.update_status(module_name, ModuleStatus.ERROR)
            
            # Emit error event
            self.event_bus.emit(
                EventType.MODULE_ERROR,
                source=module_name,
                data={'error': str(e)}
            )
    
    def _stop_module(self, module_name: str):
        """Stop a specific module."""
        module = self.registry.get(module_name)
        if not module:
            return
        
        try:
            # Stop module if it has a stop method
            if hasattr(module.instance, 'stop'):
                module.instance.stop()
            
            # Mark as stopped
            self.registry.update_status(module_name, ModuleStatus.STOPPED)
            
            self.logger.info(f"Stopped module: {module_name}")
            
            # Emit event
            self.event_bus.emit(
                EventType.MODULE_STOPPED,
                source=module_name,
                data={'module': module_name}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to stop module {module_name}: {e}")
    
    def _perform_health_checks(self):
        """Perform health checks on all modules."""
        results = self.health_monitor.check_all()
        
        # Log unhealthy modules
        for component, result in results.items():
            if result.status == HealthStatus.UNHEALTHY:
                self.logger.warning(
                    f"Module {component} is unhealthy: {result.message}"
                )
    
    def execute_pipeline(
        self,
        asset: str,
        pipeline_config: Optional[Dict] = None
    ) -> Dict:
        """
        Execute the full prediction pipeline for an asset.
        
        Args:
            asset: Asset identifier
            pipeline_config: Optional pipeline configuration
        
        Returns:
            Dictionary with pipeline results
        """
        results = {}
        
        try:
            # 1. Data Ingestion
            self.logger.info(f"Fetching data for {asset}")
            # Would call data ingestion module
            results['data_fetched'] = True
            
            # 2. Feature Engineering
            self.logger.info(f"Computing features for {asset}")
            # Would call feature engineering module
            results['features_computed'] = True
            
            # 3. Prediction
            self.logger.info(f"Making prediction for {asset}")
            # Would call prediction core module
            results['prediction_made'] = True
            
            # 4. Risk Assessment
            self.logger.info(f"Assessing risk for {asset}")
            # Would call risk management module
            results['risk_assessed'] = True
            
            # 5. Execution
            self.logger.info(f"Executing orders for {asset}")
            # Would call execution module
            results['orders_executed'] = True
            
            # 6. Monitoring
            self.logger.info(f"Recording performance for {asset}")
            # Would call monitoring module
            results['performance_recorded'] = True
            
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed for {asset}: {e}")
            results['error'] = str(e)
            return results
    
    def get_status(self) -> Dict:
        """
        Get orchestrator status.
        
        Returns:
            Dictionary with system status
        """
        return {
            'running': self.running,
            'system_health': self.health_monitor.get_system_status().value,
            'modules': self.registry.get_summary(),
            'tasks': {
                'scheduled': len(self.scheduler.list_tasks()),
                'active': len([
                    t for t in self.scheduler.list_tasks()
                    if t.status.value in ['scheduled', 'running']
                ])
            },
            'circuit_breakers': self.circuit_breakers.get_all_stats()
        }
    
    def get_module(self, name: str) -> Optional[Any]:
        """
        Get a module instance by name.
        
        Args:
            name: Module name
        
        Returns:
            Module instance or None
        """
        module = self.registry.get(name)
        return module.instance if module else None
