"""
Transaction Cost Calculator

Estimates transaction costs including commissions, spreads, and market impact.
"""

import numpy as np
from typing import Dict, Optional
from enum import Enum


class FeeStructure(Enum):
    """Commission fee structures."""
    FLAT = "flat"  # Fixed fee per trade
    PER_SHARE = "per_share"  # Fee per share
    PERCENTAGE = "percentage"  # Percentage of trade value
    TIERED = "tiered"  # Tiered based on volume


class CostCalculator:
    """
    Calculate transaction costs for orders.
    
    Includes commissions, bid-ask spread, and market impact.
    """
    
    def __init__(
        self,
        commission_rate: float = 0.001,  # 0.1% default
        fee_structure: FeeStructure = FeeStructure.PERCENTAGE,
        min_commission: float = 1.0,
        spread_bps: float = 10.0,
        market_impact_factor: float = 0.1
    ):
        """
        Initialize cost calculator.
        
        Args:
            commission_rate: Commission rate (percentage or per-share)
            fee_structure: Type of fee structure
            min_commission: Minimum commission per trade
            spread_bps: Bid-ask spread in basis points
            market_impact_factor: Market impact scaling factor
        """
        self.commission_rate = commission_rate
        self.fee_structure = fee_structure
        self.min_commission = min_commission
        self.spread_bps = spread_bps
        self.market_impact_factor = market_impact_factor
    
    def calculate_commission(
        self,
        quantity: float,
        price: float
    ) -> float:
        """
        Calculate commission cost.
        
        Args:
            quantity: Order quantity
            price: Order price
        
        Returns:
            Commission cost
        """
        trade_value = quantity * price
        
        if self.fee_structure == FeeStructure.FLAT:
            commission = self.commission_rate
        elif self.fee_structure == FeeStructure.PER_SHARE:
            commission = quantity * self.commission_rate
        elif self.fee_structure == FeeStructure.PERCENTAGE:
            commission = trade_value * self.commission_rate
        else:
            commission = trade_value * self.commission_rate
        
        # Apply minimum commission
        commission = max(commission, self.min_commission)
        
        return commission
    
    def calculate_spread_cost(
        self,
        quantity: float,
        price: float,
        is_aggressive: bool = True
    ) -> float:
        """
        Calculate cost from bid-ask spread.
        
        Args:
            quantity: Order quantity
            price: Mid price
            is_aggressive: True for market orders (cross spread)
        
        Returns:
            Spread cost
        """
        spread_fraction = self.spread_bps / 10000
        
        if is_aggressive:
            # Market orders cross the spread
            spread_cost = quantity * price * spread_fraction / 2
        else:
            # Limit orders may avoid spread cost
            spread_cost = 0
        
        return spread_cost
    
    def calculate_market_impact(
        self,
        quantity: float,
        price: float,
        average_daily_volume: Optional[float] = None
    ) -> float:
        """
        Estimate market impact cost.
        
        Market impact increases with order size relative to volume.
        
        Args:
            quantity: Order quantity
            price: Order price
            average_daily_volume: Average daily trading volume
        
        Returns:
            Market impact cost
        """
        if average_daily_volume is None or average_daily_volume == 0:
            # Default impact model based on order size
            # Impact ~ sqrt(quantity)
            impact_bps = self.market_impact_factor * np.sqrt(quantity)
        else:
            # Volume-based impact model
            # Impact ~ (quantity / volume)^0.5
            participation_rate = quantity / average_daily_volume
            impact_bps = self.market_impact_factor * np.sqrt(participation_rate) * 100
        
        impact_cost = quantity * price * (impact_bps / 10000)
        
        return impact_cost
    
    def calculate_total_cost(
        self,
        quantity: float,
        price: float,
        is_aggressive: bool = True,
        average_daily_volume: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate total transaction cost breakdown.
        
        Args:
            quantity: Order quantity
            price: Order price
            is_aggressive: True for market orders
            average_daily_volume: Average daily volume
        
        Returns:
            Dictionary with cost breakdown
        """
        commission = self.calculate_commission(quantity, price)
        spread_cost = self.calculate_spread_cost(quantity, price, is_aggressive)
        market_impact = self.calculate_market_impact(
            quantity, price, average_daily_volume
        )
        
        total_cost = commission + spread_cost + market_impact
        trade_value = quantity * price
        
        return {
            'commission': commission,
            'spread_cost': spread_cost,
            'market_impact': market_impact,
            'total_cost': total_cost,
            'cost_bps': (total_cost / trade_value) * 10000 if trade_value > 0 else 0,
            'cost_percentage': (total_cost / trade_value) * 100 if trade_value > 0 else 0
        }
    
    def calculate_slippage(
        self,
        expected_price: float,
        actual_price: float,
        quantity: float
    ) -> Dict[str, float]:
        """
        Calculate realized slippage.
        
        Args:
            expected_price: Expected execution price
            actual_price: Actual execution price
            quantity: Order quantity
        
        Returns:
            Dictionary with slippage metrics
        """
        price_diff = actual_price - expected_price
        slippage_cost = abs(price_diff) * quantity
        
        slippage_bps = (abs(price_diff) / expected_price) * 10000
        slippage_pct = (abs(price_diff) / expected_price) * 100
        
        return {
            'slippage_cost': slippage_cost,
            'slippage_bps': slippage_bps,
            'slippage_percentage': slippage_pct,
            'price_difference': price_diff
        }
    
    def estimate_net_proceeds(
        self,
        quantity: float,
        price: float,
        side: str,  # 'buy' or 'sell'
        is_aggressive: bool = True,
        average_daily_volume: Optional[float] = None
    ) -> float:
        """
        Estimate net proceeds after all costs.
        
        Args:
            quantity: Order quantity
            price: Order price
            side: 'buy' or 'sell'
            is_aggressive: True for market orders
            average_daily_volume: Average daily volume
        
        Returns:
            Net proceeds (negative for costs on buy, reduced proceeds on sell)
        """
        costs = self.calculate_total_cost(
            quantity, price, is_aggressive, average_daily_volume
        )
        
        gross_value = quantity * price
        
        if side.lower() == 'buy':
            # Buying: pay price + costs
            net = -(gross_value + costs['total_cost'])
        else:
            # Selling: receive price - costs
            net = gross_value - costs['total_cost']
        
        return net
    
    def breakeven_price(
        self,
        entry_price: float,
        quantity: float,
        side: str,  # 'buy' or 'sell'
        average_daily_volume: Optional[float] = None
    ) -> float:
        """
        Calculate breakeven price after transaction costs.
        
        Args:
            entry_price: Entry price
            quantity: Order quantity
            side: 'buy' or 'sell'
            average_daily_volume: Average daily volume
        
        Returns:
            Price needed to break even after costs
        """
        # Calculate costs for entry and exit
        entry_costs = self.calculate_total_cost(
            quantity, entry_price, True, average_daily_volume
        )
        
        # Assume exit at similar conditions
        exit_costs = self.calculate_total_cost(
            quantity, entry_price, True, average_daily_volume
        )
        
        total_costs = entry_costs['total_cost'] + exit_costs['total_cost']
        
        if side.lower() == 'buy':
            # For long: need price to rise to cover costs
            breakeven = entry_price + (total_costs / quantity)
        else:
            # For short: need price to fall to cover costs
            breakeven = entry_price - (total_costs / quantity)
        
        return breakeven
    
    def optimal_order_size(
        self,
        price: float,
        average_daily_volume: float,
        max_cost_bps: float = 50.0
    ) -> float:
        """
        Estimate optimal order size to keep costs under threshold.
        
        Args:
            price: Order price
            average_daily_volume: Average daily volume
            max_cost_bps: Maximum acceptable cost in basis points
        
        Returns:
            Optimal order quantity
        """
        # Simplified model: find quantity where total cost <= max_cost_bps
        # Use binary search
        
        min_qty = 1
        max_qty = average_daily_volume * 0.1  # Max 10% of daily volume
        
        while max_qty - min_qty > 1:
            mid_qty = (min_qty + max_qty) / 2
            costs = self.calculate_total_cost(
                mid_qty, price, True, average_daily_volume
            )
            
            if costs['cost_bps'] <= max_cost_bps:
                min_qty = mid_qty
            else:
                max_qty = mid_qty
        
        return min_qty
