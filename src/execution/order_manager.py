"""
Order Manager

Manages order lifecycle: creation, tracking, execution, and completion.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid


class OrderType(Enum):
    """Order types supported by the system."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order lifecycle statuses."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(Enum):
    """Order side: buy or sell."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    asset: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    
    metadata: Dict = field(default_factory=dict)
    
    @property
    def remaining_quantity(self) -> float:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity
    
    @property
    def is_complete(self) -> bool:
        """Check if order is in final state."""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED
        ]
    
    @property
    def fill_percentage(self) -> float:
        """Get percentage of order filled."""
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100


class OrderManager:
    """
    Manages order creation, tracking, and lifecycle.
    
    Provides centralized order management with history tracking.
    """
    
    def __init__(self):
        """Initialize order manager."""
        self.orders: Dict[str, Order] = {}
        self.active_orders: Dict[str, Order] = {}
        self.completed_orders: Dict[str, Order] = {}
    
    def create_order(
        self,
        asset: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> Order:
        """
        Create a new order.
        
        Args:
            asset: Asset identifier
            side: Buy or sell
            quantity: Order quantity
            order_type: Type of order
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            metadata: Additional order metadata
        
        Returns:
            Created Order object
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if order_type == OrderType.LIMIT and limit_price is None:
            raise ValueError("Limit orders require limit_price")
        
        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and stop_price is None:
            raise ValueError("Stop orders require stop_price")
        
        order_id = str(uuid.uuid4())
        
        order = Order(
            order_id=order_id,
            asset=asset,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            metadata=metadata or {}
        )
        
        self.orders[order_id] = order
        self.active_orders[order_id] = order
        
        return order
    
    def submit_order(self, order_id: str) -> bool:
        """
        Mark order as submitted to execution venue.
        
        Args:
            order_id: Order ID
        
        Returns:
            True if successful
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.status != OrderStatus.PENDING:
            return False
        
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = datetime.now()
        
        return True
    
    def fill_order(
        self,
        order_id: str,
        quantity: float,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record a fill for an order (full or partial).
        
        Args:
            order_id: Order ID
            quantity: Quantity filled
            price: Fill price
            timestamp: Fill timestamp
        
        Returns:
            True if successful
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.is_complete:
            return False
        
        if quantity > order.remaining_quantity:
            quantity = order.remaining_quantity
        
        # Update average fill price
        total_filled = order.filled_quantity + quantity
        order.avg_fill_price = (
            (order.filled_quantity * order.avg_fill_price + quantity * price) /
            total_filled
        )
        
        order.filled_quantity += quantity
        
        # Update status
        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
            order.filled_at = timestamp or datetime.now()
            self._move_to_completed(order_id)
        else:
            order.status = OrderStatus.PARTIAL
        
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order.
        
        Args:
            order_id: Order ID
        
        Returns:
            True if successful
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.is_complete:
            return False
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now()
        self._move_to_completed(order_id)
        
        return True
    
    def reject_order(self, order_id: str, reason: str = "") -> bool:
        """
        Mark order as rejected.
        
        Args:
            order_id: Order ID
            reason: Rejection reason
        
        Returns:
            True if successful
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.is_complete:
            return False
        
        order.status = OrderStatus.REJECTED
        order.metadata['rejection_reason'] = reason
        self._move_to_completed(order_id)
        
        return True
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order object or None
        """
        return self.orders.get(order_id)
    
    def get_active_orders(self, asset: Optional[str] = None) -> List[Order]:
        """
        Get all active orders, optionally filtered by asset.
        
        Args:
            asset: Optional asset filter
        
        Returns:
            List of active orders
        """
        orders = list(self.active_orders.values())
        
        if asset:
            orders = [o for o in orders if o.asset == asset]
        
        return orders
    
    def get_completed_orders(self, asset: Optional[str] = None) -> List[Order]:
        """
        Get completed orders, optionally filtered by asset.
        
        Args:
            asset: Optional asset filter
        
        Returns:
            List of completed orders
        """
        orders = list(self.completed_orders.values())
        
        if asset:
            orders = [o for o in orders if o.asset == asset]
        
        return orders
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Get all orders with specific status.
        
        Args:
            status: Order status
        
        Returns:
            List of orders with given status
        """
        return [o for o in self.orders.values() if o.status == status]
    
    def _move_to_completed(self, order_id: str):
        """Move order from active to completed."""
        if order_id in self.active_orders:
            order = self.active_orders.pop(order_id)
            self.completed_orders[order_id] = order
    
    def get_fill_statistics(self, asset: Optional[str] = None) -> Dict:
        """
        Get fill statistics for completed orders.
        
        Args:
            asset: Optional asset filter
        
        Returns:
            Dictionary with fill statistics
        """
        completed = self.get_completed_orders(asset)
        filled = [o for o in completed if o.status == OrderStatus.FILLED]
        
        if not filled:
            return {
                'total_orders': len(completed),
                'filled_orders': 0,
                'fill_rate': 0.0,
                'avg_fill_time': 0.0
            }
        
        # Calculate average fill time
        fill_times = []
        for order in filled:
            if order.submitted_at and order.filled_at:
                fill_time = (order.filled_at - order.submitted_at).total_seconds()
                fill_times.append(fill_time)
        
        avg_fill_time = sum(fill_times) / len(fill_times) if fill_times else 0.0
        
        return {
            'total_orders': len(completed),
            'filled_orders': len(filled),
            'fill_rate': (len(filled) / len(completed)) * 100,
            'avg_fill_time_seconds': avg_fill_time
        }
