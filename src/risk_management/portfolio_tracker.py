"""
Portfolio Tracker

Tracks portfolio positions, performance, and risk metrics over time.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Position:
    """Represents a single position in the portfolio."""
    asset: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    
    @property
    def value(self) -> float:
        """Current value of position."""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Original cost of position."""
        return self.quantity * self.entry_price
    
    @property
    def pnl(self) -> float:
        """Unrealized profit/loss."""
        return self.value - self.cost_basis
    
    @property
    def pnl_percent(self) -> float:
        """Unrealized profit/loss as percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.pnl / self.cost_basis) * 100


@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time."""
    timestamp: datetime
    total_value: float
    cash: float
    positions_value: float
    positions: Dict[str, Position]
    returns: float = 0.0


class PortfolioTracker:
    """
    Track portfolio positions, performance, and risk metrics.
    
    Maintains current positions and historical performance data.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize portfolio tracker.
        
        Args:
            initial_capital: Starting capital amount
        """
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.history: List[PortfolioSnapshot] = []
        
        # Performance tracking
        self.realized_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def add_position(
        self,
        asset: str,
        quantity: float,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Add or increase a position.
        
        Args:
            asset: Asset identifier
            quantity: Quantity to add (positive for long, negative for short)
            price: Entry price
            timestamp: Time of entry
        
        Returns:
            True if successful, False if insufficient capital
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        cost = abs(quantity * price)
        
        # Check if enough cash
        if cost > self.cash:
            return False
        
        # Update or create position
        if asset in self.positions:
            # Average in for simplicity
            existing = self.positions[asset]
            total_quantity = existing.quantity + quantity
            avg_price = (
                (existing.quantity * existing.entry_price + quantity * price) /
                total_quantity
            )
            existing.quantity = total_quantity
            existing.entry_price = avg_price
            existing.current_price = price
        else:
            self.positions[asset] = Position(
                asset=asset,
                quantity=quantity,
                entry_price=price,
                entry_time=timestamp,
                current_price=price
            )
        
        self.cash -= cost
        self.total_trades += 1
        
        return True
    
    def close_position(
        self,
        asset: str,
        price: float,
        quantity: Optional[float] = None
    ) -> Optional[float]:
        """
        Close a position (partial or full).
        
        Args:
            asset: Asset identifier
            price: Exit price
            quantity: Quantity to close (None for full position)
        
        Returns:
            Realized PnL from closing position, or None if position doesn't exist
        """
        if asset not in self.positions:
            return None
        
        position = self.positions[asset]
        
        # Determine quantity to close
        if quantity is None:
            quantity = position.quantity
        else:
            quantity = min(quantity, position.quantity)
        
        # Calculate realized PnL
        pnl = quantity * (price - position.entry_price)
        self.realized_pnl += pnl
        self.cash += quantity * price
        
        # Update trade statistics
        if pnl > 0:
            self.winning_trades += 1
        elif pnl < 0:
            self.losing_trades += 1
        
        # Update or remove position
        position.quantity -= quantity
        if position.quantity <= 0:
            del self.positions[asset]
        
        return pnl
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions.
        
        Args:
            prices: Dictionary mapping asset to current price
        """
        for asset, position in self.positions.items():
            if asset in prices:
                position.current_price = prices[asset]
    
    def get_portfolio_value(self) -> float:
        """
        Get total portfolio value (cash + positions).
        
        Returns:
            Total portfolio value
        """
        positions_value = sum(pos.value for pos in self.positions.values())
        return self.cash + positions_value
    
    def get_positions_value(self) -> float:
        """
        Get total value of all positions.
        
        Returns:
            Total positions value
        """
        return sum(pos.value for pos in self.positions.values())
    
    def get_unrealized_pnl(self) -> float:
        """
        Get total unrealized profit/loss.
        
        Returns:
            Total unrealized PnL
        """
        return sum(pos.pnl for pos in self.positions.values())
    
    def get_total_pnl(self) -> float:
        """
        Get total profit/loss (realized + unrealized).
        
        Returns:
            Total PnL
        """
        return self.realized_pnl + self.get_unrealized_pnl()
    
    def get_return(self) -> float:
        """
        Get portfolio return as percentage.
        
        Returns:
            Portfolio return percentage
        """
        current_value = self.get_portfolio_value()
        return ((current_value - self.initial_capital) / self.initial_capital) * 100
    
    def get_position_weights(self) -> Dict[str, float]:
        """
        Get position weights as fraction of portfolio.
        
        Returns:
            Dictionary mapping asset to weight (0-1)
        """
        total_value = self.get_portfolio_value()
        if total_value == 0:
            return {}
        
        return {
            asset: pos.value / total_value
            for asset, pos in self.positions.items()
        }
    
    def take_snapshot(self, timestamp: Optional[datetime] = None) -> PortfolioSnapshot:
        """
        Take a snapshot of current portfolio state.
        
        Args:
            timestamp: Time of snapshot
        
        Returns:
            PortfolioSnapshot object
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        total_value = self.get_portfolio_value()
        positions_value = self.get_positions_value()
        
        # Calculate returns since last snapshot
        returns = 0.0
        if self.history:
            last_value = self.history[-1].total_value
            if last_value > 0:
                returns = (total_value - last_value) / last_value
        
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            total_value=total_value,
            cash=self.cash,
            positions_value=positions_value,
            positions=self.positions.copy(),
            returns=returns
        )
        
        self.history.append(snapshot)
        return snapshot
    
    def get_historical_returns(self) -> np.ndarray:
        """
        Get historical returns from snapshots.
        
        Returns:
            Array of returns
        """
        if len(self.history) < 2:
            return np.array([])
        
        returns = [snapshot.returns for snapshot in self.history[1:]]
        return np.array(returns)
    
    def get_max_drawdown(self) -> Tuple[float, datetime, datetime]:
        """
        Calculate maximum drawdown from history.
        
        Returns:
            Tuple of (max_drawdown_percent, peak_time, trough_time)
        """
        if len(self.history) < 2:
            return 0.0, datetime.now(), datetime.now()
        
        values = np.array([s.total_value for s in self.history])
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdown at each point
        drawdowns = (values - running_max) / running_max * 100
        
        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdowns)
        max_dd = drawdowns[max_dd_idx]
        
        # Find peak before max drawdown
        peak_idx = np.argmax(values[:max_dd_idx + 1])
        
        return abs(max_dd), self.history[peak_idx].timestamp, self.history[max_dd_idx].timestamp
    
    def get_win_rate(self) -> float:
        """
        Calculate win rate (winning trades / total trades).
        
        Returns:
            Win rate as percentage
        """
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    def get_summary(self) -> Dict:
        """
        Get portfolio summary statistics.
        
        Returns:
            Dictionary with summary metrics
        """
        total_value = self.get_portfolio_value()
        returns = self.get_return()
        max_dd, peak_time, trough_time = self.get_max_drawdown()
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'cash': self.cash,
            'positions_value': self.get_positions_value(),
            'total_return_pct': returns,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.get_unrealized_pnl(),
            'total_pnl': self.get_total_pnl(),
            'num_positions': len(self.positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate_pct': self.get_win_rate(),
            'max_drawdown_pct': max_dd,
        }
