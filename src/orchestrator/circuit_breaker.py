"""
Circuit Breaker

Implements circuit breaker pattern for fault tolerance.
"""

from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.
    
    Prevents cascading failures by temporarily blocking calls to
    failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Time to wait before trying again (half-open)
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.expected_exception = expected_exception
        
        self.logger = logging.getLogger(__name__)
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
    
    def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open or function fails
        """
        self.stats.total_calls += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.stats.rejected_calls += 1
                raise Exception("Circuit breaker is OPEN")
        
        # Try to execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.stats.successful_calls += 1
        self.stats.last_success_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Success in half-open state -> close circuit
            self._transition_to_closed()
        
        # Reset failure count on success
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.stats.failed_calls += 1
        self.stats.last_failure_time = datetime.now()
        self.last_failure_time = datetime.now()
        self.failure_count += 1
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try again."""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure >= self.timeout
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.logger.info("Circuit breaker transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.stats.state_changes += 1
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.logger.warning("Circuit breaker transitioning to OPEN")
        self.state = CircuitState.OPEN
        self.stats.state_changes += 1
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.logger.info("Circuit breaker transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.stats.state_changes += 1
    
    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        self.logger.info("Manually resetting circuit breaker")
        self._transition_to_closed()
    
    def force_open(self):
        """Manually open circuit breaker."""
        self.logger.warning("Manually opening circuit breaker")
        self._transition_to_open()
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self.stats
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def is_available(self) -> bool:
        """Check if circuit breaker allows calls."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.HALF_OPEN:
            return True
        else:  # OPEN
            return self._should_attempt_reset()


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        """Initialize circuit breaker registry."""
        self.breakers: dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.
        
        Args:
            name: Circuit breaker name
            failure_threshold: Failure threshold
            timeout_seconds: Timeout in seconds
            expected_exception: Exception type to catch
        
        Returns:
            CircuitBreaker instance
        """
        if name in self.breakers:
            return self.breakers[name]
        
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds,
            expected_exception=expected_exception
        )
        
        self.breakers[name] = breaker
        self.logger.info(f"Registered circuit breaker: {name}")
        
        return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.breakers.get(name)
    
    def get_all_stats(self) -> dict[str, dict]:
        """Get statistics for all circuit breakers."""
        return {
            name: {
                'state': breaker.get_state().value,
                'stats': {
                    'total_calls': breaker.stats.total_calls,
                    'successful_calls': breaker.stats.successful_calls,
                    'failed_calls': breaker.stats.failed_calls,
                    'rejected_calls': breaker.stats.rejected_calls,
                    'state_changes': breaker.stats.state_changes
                }
            }
            for name, breaker in self.breakers.items()
        }
