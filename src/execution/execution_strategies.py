"""
Execution Strategies

Implements various order execution strategies: TWAP, VWAP, Limit orders.
"""

import numpy as np
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .order_manager import Order, OrderManager, OrderType, OrderSide


class ExecutionStrategy(ABC):
    """Base class for execution strategies."""
    
    @abstractmethod
    def split_order(
        self,
        total_quantity: float,
        **kwargs
    ) -> List[Dict]:
        """
        Split order into smaller child orders.
        
        Returns:
            List of child order specifications
        """
        pass


class TWAPStrategy(ExecutionStrategy):
    """
    Time-Weighted Average Price (TWAP) execution strategy.
    
    Splits order into equal-sized slices executed at regular intervals.
    """
    
    def __init__(
        self,
        duration_minutes: int = 60,
        num_slices: int = 10
    ):
        """
        Initialize TWAP strategy.
        
        Args:
            duration_minutes: Total execution duration
            num_slices: Number of order slices
        """
        self.duration_minutes = duration_minutes
        self.num_slices = num_slices
    
    def split_order(
        self,
        total_quantity: float,
        start_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Split order into equal-sized slices.
        
        Args:
            total_quantity: Total quantity to execute
            start_time: Start time for execution
        
        Returns:
            List of child order specifications
        """
        if start_time is None:
            start_time = datetime.now()
        
        slice_quantity = total_quantity / self.num_slices
        interval_minutes = self.duration_minutes / self.num_slices
        
        child_orders = []
        for i in range(self.num_slices):
            execution_time = start_time + timedelta(minutes=i * interval_minutes)
            
            child_orders.append({
                'quantity': slice_quantity,
                'execution_time': execution_time,
                'slice_number': i + 1
            })
        
        return child_orders


class VWAPStrategy(ExecutionStrategy):
    """
    Volume-Weighted Average Price (VWAP) execution strategy.
    
    Splits order based on expected volume distribution throughout the day.
    """
    
    def __init__(
        self,
        duration_minutes: int = 60,
        volume_profile: Optional[List[float]] = None
    ):
        """
        Initialize VWAP strategy.
        
        Args:
            duration_minutes: Total execution duration
            volume_profile: Expected volume distribution (normalized)
        """
        self.duration_minutes = duration_minutes
        
        # Default intraday volume profile (U-shaped)
        if volume_profile is None:
            # Higher volume at open and close
            self.volume_profile = self._default_volume_profile()
        else:
            self.volume_profile = np.array(volume_profile)
            self.volume_profile = self.volume_profile / np.sum(self.volume_profile)
    
    def _default_volume_profile(self) -> np.ndarray:
        """
        Create default U-shaped intraday volume profile.
        
        Returns:
            Normalized volume profile
        """
        # Typical U-shaped intraday pattern
        # High volume at open, declining through day, rising at close
        profile = np.array([
            0.15, 0.12, 0.10, 0.08, 0.07,  # Morning
            0.06, 0.06, 0.06, 0.07, 0.08,  # Midday to afternoon
            0.10, 0.12, 0.15                 # Close
        ])
        return profile / np.sum(profile)
    
    def split_order(
        self,
        total_quantity: float,
        start_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Split order according to volume profile.
        
        Args:
            total_quantity: Total quantity to execute
            start_time: Start time for execution
        
        Returns:
            List of child order specifications
        """
        if start_time is None:
            start_time = datetime.now()
        
        num_slices = len(self.volume_profile)
        interval_minutes = self.duration_minutes / num_slices
        
        child_orders = []
        for i, volume_weight in enumerate(self.volume_profile):
            slice_quantity = total_quantity * volume_weight
            execution_time = start_time + timedelta(minutes=i * interval_minutes)
            
            child_orders.append({
                'quantity': slice_quantity,
                'execution_time': execution_time,
                'slice_number': i + 1,
                'volume_weight': volume_weight
            })
        
        return child_orders


class LimitOrderStrategy(ExecutionStrategy):
    """
    Passive limit order execution strategy.
    
    Places limit orders at specified price levels with patience.
    """
    
    def __init__(
        self,
        limit_price: float,
        improvement_ticks: int = 0,
        max_wait_minutes: int = 60
    ):
        """
        Initialize limit order strategy.
        
        Args:
            limit_price: Base limit price
            improvement_ticks: Number of ticks to improve price
            max_wait_minutes: Maximum time to wait for fill
        """
        self.limit_price = limit_price
        self.improvement_ticks = improvement_ticks
        self.max_wait_minutes = max_wait_minutes
    
    def split_order(
        self,
        total_quantity: float,
        tick_size: float = 0.01,
        start_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Create limit order at specified price.
        
        Args:
            total_quantity: Total quantity to execute
            tick_size: Minimum price increment
            start_time: Start time
        
        Returns:
            List with single limit order specification
        """
        if start_time is None:
            start_time = datetime.now()
        
        # Adjust limit price by improvement ticks
        adjusted_limit = self.limit_price + (self.improvement_ticks * tick_size)
        
        return [{
            'quantity': total_quantity,
            'limit_price': adjusted_limit,
            'execution_time': start_time,
            'max_wait_until': start_time + timedelta(minutes=self.max_wait_minutes)
        }]


class AdaptiveStrategy(ExecutionStrategy):
    """
    Adaptive execution strategy.
    
    Adjusts execution based on market conditions and fill rates.
    """
    
    def __init__(
        self,
        target_duration_minutes: int = 60,
        urgency: float = 0.5,
        participation_rate: float = 0.1
    ):
        """
        Initialize adaptive strategy.
        
        Args:
            target_duration_minutes: Target execution duration
            urgency: Urgency level (0=patient, 1=aggressive)
            participation_rate: Target participation in market volume
        """
        self.target_duration_minutes = target_duration_minutes
        self.urgency = urgency
        self.participation_rate = participation_rate
    
    def split_order(
        self,
        total_quantity: float,
        current_market_volume: Optional[float] = None,
        start_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Split order adaptively based on urgency and market conditions.
        
        Args:
            total_quantity: Total quantity to execute
            current_market_volume: Current market volume
            start_time: Start time
        
        Returns:
            List of child order specifications
        """
        if start_time is None:
            start_time = datetime.now()
        
        # More urgent = fewer, larger slices
        # Less urgent = more, smaller slices
        num_slices = max(5, int(20 * (1 - self.urgency)))
        
        # Adjust slice sizes based on market volume
        if current_market_volume is not None:
            # Limit each slice to participation rate
            max_slice = current_market_volume * self.participation_rate
            slice_quantity = min(total_quantity / num_slices, max_slice)
            num_slices = int(np.ceil(total_quantity / slice_quantity))
        else:
            slice_quantity = total_quantity / num_slices
        
        interval_minutes = self.target_duration_minutes / num_slices
        
        child_orders = []
        remaining_quantity = total_quantity
        
        for i in range(num_slices):
            current_slice = min(slice_quantity, remaining_quantity)
            execution_time = start_time + timedelta(minutes=i * interval_minutes)
            
            child_orders.append({
                'quantity': current_slice,
                'execution_time': execution_time,
                'slice_number': i + 1,
                'urgency': self.urgency
            })
            
            remaining_quantity -= current_slice
            if remaining_quantity <= 0:
                break
        
        return child_orders
    
    def adjust_strategy(
        self,
        filled_quantity: float,
        total_quantity: float,
        elapsed_time_minutes: float
    ) -> float:
        """
        Adjust strategy based on execution progress.
        
        Args:
            filled_quantity: Quantity filled so far
            total_quantity: Total target quantity
            elapsed_time_minutes: Time elapsed
        
        Returns:
            Adjusted urgency level
        """
        fill_rate = filled_quantity / total_quantity if total_quantity > 0 else 0
        time_progress = elapsed_time_minutes / self.target_duration_minutes
        
        # If we're behind schedule, increase urgency
        if fill_rate < time_progress:
            urgency_adjustment = (time_progress - fill_rate) * 0.5
            new_urgency = min(1.0, self.urgency + urgency_adjustment)
        else:
            # If ahead of schedule, can reduce urgency
            urgency_adjustment = (fill_rate - time_progress) * 0.3
            new_urgency = max(0.0, self.urgency - urgency_adjustment)
        
        return new_urgency
