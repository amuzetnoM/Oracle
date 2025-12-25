"""
Health Monitor

Monitors system and module health.
"""

from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


class HealthStatus(Enum):
    """Health check statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""
    component: str
    status: HealthStatus
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class HealthMonitor:
    """
    Monitor health of system components.
    
    Performs periodic health checks and alerts on issues.
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 60
    ):
        """
        Initialize health monitor.
        
        Args:
            check_interval_seconds: Interval between health checks
        """
        self.logger = logging.getLogger(__name__)
        self.check_interval = check_interval_seconds
        
        # Health check functions: component -> check_function
        self.health_checks: Dict[str, Callable[[], HealthCheck]] = {}
        
        # Health history
        self.health_history: Dict[str, List[HealthCheck]] = {}
        self.max_history_per_component = 100
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[HealthCheck], None]] = []
    
    def register_health_check(
        self,
        component: str,
        check_function: Callable[[], HealthCheck]
    ):
        """
        Register a health check for a component.
        
        Args:
            component: Component name
            check_function: Function that performs health check
        """
        self.health_checks[component] = check_function
        self.logger.info(f"Registered health check for: {component}")
    
    def unregister_health_check(self, component: str):
        """
        Unregister a health check.
        
        Args:
            component: Component name
        """
        if component in self.health_checks:
            del self.health_checks[component]
            self.logger.info(f"Unregistered health check for: {component}")
    
    def register_alert_callback(
        self,
        callback: Callable[[HealthCheck], None]
    ):
        """
        Register callback for health alerts.
        
        Args:
            callback: Function to call on unhealthy status
        """
        self.alert_callbacks.append(callback)
    
    def check_component(self, component: str) -> Optional[HealthCheck]:
        """
        Run health check for a specific component.
        
        Args:
            component: Component name
        
        Returns:
            HealthCheck result or None if not registered
        """
        if component not in self.health_checks:
            return None
        
        try:
            check_result = self.health_checks[component]()
            self._record_health(check_result)
            
            # Alert if unhealthy
            if check_result.status == HealthStatus.UNHEALTHY:
                self._trigger_alerts(check_result)
            
            return check_result
            
        except Exception as e:
            self.logger.error(f"Health check failed for {component}: {e}")
            check_result = HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}"
            )
            self._record_health(check_result)
            self._trigger_alerts(check_result)
            return check_result
    
    def check_all(self) -> Dict[str, HealthCheck]:
        """
        Run all registered health checks.
        
        Returns:
            Dictionary mapping component to health check result
        """
        results = {}
        
        for component in self.health_checks:
            result = self.check_component(component)
            if result:
                results[component] = result
        
        return results
    
    def get_system_status(self) -> HealthStatus:
        """
        Get overall system health status.
        
        Returns:
            Overall health status
        """
        if not self.health_checks:
            return HealthStatus.UNKNOWN
        
        results = self.check_all()
        
        if not results:
            return HealthStatus.UNKNOWN
        
        # System is unhealthy if any component is unhealthy
        if any(r.status == HealthStatus.UNHEALTHY for r in results.values()):
            return HealthStatus.UNHEALTHY
        
        # System is degraded if any component is degraded
        if any(r.status == HealthStatus.DEGRADED for r in results.values()):
            return HealthStatus.DEGRADED
        
        # All healthy
        return HealthStatus.HEALTHY
    
    def _record_health(self, check: HealthCheck):
        """Record health check in history."""
        if check.component not in self.health_history:
            self.health_history[check.component] = []
        
        self.health_history[check.component].append(check)
        
        # Limit history size
        if len(self.health_history[check.component]) > self.max_history_per_component:
            self.health_history[check.component].pop(0)
    
    def _trigger_alerts(self, check: HealthCheck):
        """Trigger alert callbacks for unhealthy status."""
        for callback in self.alert_callbacks:
            try:
                callback(check)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def get_history(
        self,
        component: str,
        limit: int = 50
    ) -> List[HealthCheck]:
        """
        Get health check history for a component.
        
        Args:
            component: Component name
            limit: Maximum number of records
        
        Returns:
            List of health checks
        """
        if component not in self.health_history:
            return []
        
        return self.health_history[component][-limit:]
    
    def get_uptime(self, component: str) -> Optional[float]:
        """
        Calculate uptime percentage for a component.
        
        Args:
            component: Component name
        
        Returns:
            Uptime percentage (0-100) or None
        """
        history = self.get_history(component)
        
        if not history:
            return None
        
        healthy_count = sum(
            1 for check in history
            if check.status == HealthStatus.HEALTHY
        )
        
        return (healthy_count / len(history)) * 100
    
    def get_summary(self) -> Dict:
        """
        Get health summary for all components.
        
        Returns:
            Dictionary with health summary
        """
        summary = {
            'system_status': self.get_system_status().value,
            'components': {}
        }
        
        for component in self.health_checks:
            latest = self.health_history.get(component, [])
            if latest:
                latest_check = latest[-1]
                summary['components'][component] = {
                    'status': latest_check.status.value,
                    'message': latest_check.message,
                    'last_check': latest_check.timestamp.isoformat(),
                    'uptime_pct': self.get_uptime(component)
                }
            else:
                summary['components'][component] = {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': 'No health checks performed yet'
                }
        
        return summary
    
    def is_healthy(self, component: str) -> bool:
        """
        Check if component is currently healthy.
        
        Args:
            component: Component name
        
        Returns:
            True if healthy
        """
        history = self.health_history.get(component, [])
        if not history:
            return False
        
        latest = history[-1]
        return latest.status == HealthStatus.HEALTHY
