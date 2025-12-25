"""
Event Bus

Publish-subscribe event system for module communication.
"""

from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging


class EventType(Enum):
    """System event types."""
    # Data events
    DATA_FETCHED = "data_fetched"
    DATA_ERROR = "data_error"
    
    # Feature events
    FEATURES_COMPUTED = "features_computed"
    FEATURES_ERROR = "features_error"
    
    # Prediction events
    PREDICTION_MADE = "prediction_made"
    PREDICTION_ERROR = "prediction_error"
    
    # Risk events
    RISK_ASSESSED = "risk_assessed"
    POSITION_SIZED = "position_sized"
    
    # Execution events
    ORDER_CREATED = "order_created"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    
    # Monitoring events
    PERFORMANCE_UPDATED = "performance_updated"
    DRIFT_DETECTED = "drift_detected"
    
    # System events
    MODULE_STARTED = "module_started"
    MODULE_STOPPED = "module_stopped"
    MODULE_ERROR = "module_error"
    HEALTH_CHECK = "health_check"
    
    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """Event object passed through the event bus."""
    event_type: EventType
    source: str  # Module that generated the event
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: Optional[str] = None


class EventBus:
    """
    Event bus for publish-subscribe messaging between modules.
    
    Enables loose coupling between system components.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self.logger = logging.getLogger(__name__)
        
        # Subscribers: event_type -> list of callbacks
        self.subscribers: Dict[EventType, List[Callable]] = {}
        
        # Event history for debugging
        self.event_history: List[Event] = []
        self.max_history = 1000
    
    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None]
    ):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                self.logger.debug(f"Unsubscribed from {event_type}")
            except ValueError:
                pass
    
    def publish(self, event: Event):
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify subscribers
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    self.logger.error(
                        f"Error in event callback for {event.event_type}: {e}"
                    )
    
    def emit(
        self,
        event_type: EventType,
        source: str,
        data: Optional[Dict] = None
    ):
        """
        Convenience method to create and publish an event.
        
        Args:
            event_type: Type of event
            source: Source module
            data: Event data
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {}
        )
        self.publish(event)
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
        
        Returns:
            List of events
        """
        history = self.event_history
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        return history[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
    
    def subscriber_count(self, event_type: EventType) -> int:
        """
        Get number of subscribers for an event type.
        
        Args:
            event_type: Event type
        
        Returns:
            Number of subscribers
        """
        return len(self.subscribers.get(event_type, []))
    
    def get_all_subscribers(self) -> Dict[EventType, int]:
        """
        Get subscriber counts for all event types.
        
        Returns:
            Dictionary mapping event type to subscriber count
        """
        return {
            event_type: len(callbacks)
            for event_type, callbacks in self.subscribers.items()
        }
