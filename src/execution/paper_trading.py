"""
Paper Trading

Simulated order execution for backtesting and testing.
Simulates realistic market behavior with slippage and delays.
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta

from .order_manager import (
    OrderManager, Order, OrderStatus, OrderType, OrderSide
)
from .cost_calculator import CostCalculator


class PaperTrading:
    """
    Paper trading engine that simulates order execution.
    
    Provides realistic simulation of market orders with slippage,
    delays, and transaction costs.
    """
    
    def __init__(
        self,
        order_manager: OrderManager,
        cost_calculator: Optional[CostCalculator] = None,
        slippage_bps: float = 5.0,
        execution_delay_seconds: float = 1.0,
        fill_probability: float = 0.95
    ):
        """
        Initialize paper trading engine.
        
        Args:
            order_manager: Order manager instance
            cost_calculator: Transaction cost calculator
            slippage_bps: Average slippage in basis points
            execution_delay_seconds: Simulated execution delay
            fill_probability: Probability of order being filled (for limit orders)
        """
        self.order_manager = order_manager
        self.cost_calculator = cost_calculator or CostCalculator()
        self.slippage_bps = slippage_bps
        self.execution_delay_seconds = execution_delay_seconds
        self.fill_probability = fill_probability
        
        # Track current market prices
        self.market_prices: Dict[str, float] = {}
    
    def update_market_price(self, asset: str, price: float):
        """
        Update current market price for an asset.
        
        Args:
            asset: Asset identifier
            price: Current market price
        """
        self.market_prices[asset] = price
    
    def update_market_prices(self, prices: Dict[str, float]):
        """
        Update market prices for multiple assets.
        
        Args:
            prices: Dictionary mapping asset to price
        """
        self.market_prices.update(prices)
    
    def execute_order(
        self,
        order: Order,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Execute an order in paper trading.
        
        Args:
            order: Order to execute
            current_time: Current simulation time
        
        Returns:
            True if order was filled
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if we have market price
        if order.asset not in self.market_prices:
            self.order_manager.reject_order(
                order.order_id,
                reason=f"No market price available for {order.asset}"
            )
            return False
        
        market_price = self.market_prices[order.asset]
        
        # Submit the order
        self.order_manager.submit_order(order.order_id)
        
        # Simulate execution based on order type
        if order.order_type == OrderType.MARKET:
            return self._execute_market_order(order, market_price, current_time)
        elif order.order_type == OrderType.LIMIT:
            return self._execute_limit_order(order, market_price, current_time)
        elif order.order_type == OrderType.STOP:
            return self._execute_stop_order(order, market_price, current_time)
        else:
            self.order_manager.reject_order(
                order.order_id,
                reason=f"Order type {order.order_type} not supported"
            )
            return False
    
    def _execute_market_order(
        self,
        order: Order,
        market_price: float,
        current_time: datetime
    ) -> bool:
        """Execute a market order with slippage."""
        # Calculate slippage
        slippage = self._calculate_slippage(market_price, order.quantity)
        
        # Adjust price based on side (buy = higher, sell = lower)
        if order.side == OrderSide.BUY:
            fill_price = market_price * (1 + slippage)
        else:
            fill_price = market_price * (1 - slippage)
        
        # Simulate execution delay
        fill_time = current_time + timedelta(seconds=self.execution_delay_seconds)
        
        # Fill the order
        success = self.order_manager.fill_order(
            order.order_id,
            quantity=order.quantity,
            price=fill_price,
            timestamp=fill_time
        )
        
        return success
    
    def _execute_limit_order(
        self,
        order: Order,
        market_price: float,
        current_time: datetime
    ) -> bool:
        """Execute a limit order if price conditions are met."""
        if order.limit_price is None:
            return False
        
        # Check if limit price is acceptable
        if order.side == OrderSide.BUY:
            # Buy limit: execute if market price <= limit price
            if market_price > order.limit_price:
                return False
        else:
            # Sell limit: execute if market price >= limit price
            if market_price < order.limit_price:
                return False
        
        # Simulate probability of fill (limit orders may not always fill)
        if np.random.random() > self.fill_probability:
            return False
        
        # Fill at limit price (or better)
        fill_price = order.limit_price
        fill_time = current_time + timedelta(seconds=self.execution_delay_seconds)
        
        success = self.order_manager.fill_order(
            order.order_id,
            quantity=order.quantity,
            price=fill_price,
            timestamp=fill_time
        )
        
        return success
    
    def _execute_stop_order(
        self,
        order: Order,
        market_price: float,
        current_time: datetime
    ) -> bool:
        """Execute a stop order if price conditions are met."""
        if order.stop_price is None:
            return False
        
        # Check if stop is triggered
        if order.side == OrderSide.BUY:
            # Buy stop: trigger if market price >= stop price
            if market_price < order.stop_price:
                return False
        else:
            # Sell stop: trigger if market price <= stop price
            if market_price > order.stop_price:
                return False
        
        # Once triggered, execute as market order
        return self._execute_market_order(order, market_price, current_time)
    
    def _calculate_slippage(self, price: float, quantity: float) -> float:
        """
        Calculate slippage as fraction of price.
        
        Slippage increases with order size (square root model).
        
        Args:
            price: Market price
            quantity: Order quantity
        
        Returns:
            Slippage as fraction (e.g., 0.0005 for 5 bps)
        """
        # Base slippage in basis points
        base_slippage = self.slippage_bps / 10000
        
        # Adjust for quantity (larger orders have more slippage)
        # Use square root to model market impact
        quantity_factor = np.sqrt(max(1, quantity / 100))
        
        # Add random component
        random_factor = 1 + np.random.normal(0, 0.2)
        
        slippage = base_slippage * quantity_factor * random_factor
        
        return max(0, slippage)
    
    def process_active_orders(self, current_time: Optional[datetime] = None):
        """
        Process all active orders against current market prices.
        
        Args:
            current_time: Current simulation time
        """
        if current_time is None:
            current_time = datetime.now()
        
        active_orders = self.order_manager.get_active_orders()
        
        for order in active_orders:
            if order.status == OrderStatus.PENDING:
                self.execute_order(order, current_time)
            elif order.status == OrderStatus.SUBMITTED:
                # Try to execute already submitted orders
                if order.asset in self.market_prices:
                    market_price = self.market_prices[order.asset]
                    
                    if order.order_type == OrderType.LIMIT:
                        self._execute_limit_order(order, market_price, current_time)
                    elif order.order_type == OrderType.STOP:
                        self._execute_stop_order(order, market_price, current_time)
    
    def get_execution_summary(self) -> Dict:
        """
        Get summary of paper trading execution.
        
        Returns:
            Dictionary with execution statistics
        """
        stats = self.order_manager.get_fill_statistics()
        
        # Calculate average slippage from filled orders
        filled_orders = self.order_manager.get_orders_by_status(OrderStatus.FILLED)
        
        if filled_orders:
            slippages = []
            for order in filled_orders:
                if order.asset in self.market_prices:
                    market_price = self.market_prices[order.asset]
                    slippage_pct = abs(
                        (order.avg_fill_price - market_price) / market_price
                    ) * 100
                    slippages.append(slippage_pct)
            
            avg_slippage = np.mean(slippages) if slippages else 0.0
        else:
            avg_slippage = 0.0
        
        stats['avg_slippage_pct'] = avg_slippage
        
        return stats
