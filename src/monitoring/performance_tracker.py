"""
Performance Tracker

Tracks predictions, outcomes, and performance metrics over time.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TradeRecord:
    """Record of a single trade."""
    timestamp: datetime
    asset: str
    prediction: str  # 'up', 'down', 'flat'
    confidence: float
    entry_price: float
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    correct: Optional[bool] = None
    metadata: Dict = field(default_factory=dict)


class PerformanceTracker:
    """
    Track system performance over time.
    
    Records predictions, outcomes, and calculates performance metrics.
    """
    
    def __init__(self):
        """Initialize performance tracker."""
        self.trades: List[TradeRecord] = []
        self.predictions: List[Dict] = []
        self.outcomes: List[Dict] = []
    
    def record_prediction(
        self,
        asset: str,
        prediction: str,
        confidence: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Record a prediction.
        
        Args:
            asset: Asset identifier
            prediction: Predicted direction ('up', 'down', 'flat')
            confidence: Confidence score (0-1)
            timestamp: Prediction timestamp
            metadata: Additional metadata
        
        Returns:
            Prediction ID (index)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        prediction_record = {
            'prediction_id': len(self.predictions),
            'timestamp': timestamp,
            'asset': asset,
            'prediction': prediction,
            'confidence': confidence,
            'metadata': metadata or {}
        }
        
        self.predictions.append(prediction_record)
        return prediction_record['prediction_id']
    
    def record_outcome(
        self,
        prediction_id: int,
        actual_direction: str,
        pnl: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record the outcome of a prediction.
        
        Args:
            prediction_id: ID of the original prediction
            actual_direction: Actual direction ('up', 'down', 'flat')
            pnl: Profit/loss amount
            timestamp: Outcome timestamp
        """
        if prediction_id >= len(self.predictions):
            raise ValueError(f"Invalid prediction_id: {prediction_id}")
        
        if timestamp is None:
            timestamp = datetime.now()
        
        prediction = self.predictions[prediction_id]
        
        correct = prediction['prediction'] == actual_direction
        
        outcome_record = {
            'prediction_id': prediction_id,
            'timestamp': timestamp,
            'actual_direction': actual_direction,
            'pnl': pnl,
            'correct': correct
        }
        
        self.outcomes.append(outcome_record)
    
    def record_trade(
        self,
        asset: str,
        prediction: str,
        confidence: float,
        entry_price: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> TradeRecord:
        """
        Record a new trade.
        
        Args:
            asset: Asset identifier
            prediction: Predicted direction
            confidence: Confidence score
            entry_price: Entry price
            timestamp: Entry timestamp
            metadata: Additional metadata
        
        Returns:
            TradeRecord object
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        trade = TradeRecord(
            timestamp=timestamp,
            asset=asset,
            prediction=prediction,
            confidence=confidence,
            entry_price=entry_price,
            metadata=metadata or {}
        )
        
        self.trades.append(trade)
        return trade
    
    def close_trade(
        self,
        trade: TradeRecord,
        exit_price: float,
        exit_time: Optional[datetime] = None
    ):
        """
        Close a trade and calculate results.
        
        Args:
            trade: Trade to close
            exit_price: Exit price
            exit_time: Exit timestamp
        """
        if exit_time is None:
            exit_time = datetime.now()
        
        trade.exit_price = exit_price
        trade.exit_time = exit_time
        
        # Calculate PnL
        price_change = exit_price - trade.entry_price
        trade.pnl = price_change
        trade.pnl_percent = (price_change / trade.entry_price) * 100
        
        # Determine if prediction was correct
        if trade.prediction == 'up':
            trade.correct = price_change > 0
        elif trade.prediction == 'down':
            trade.correct = price_change < 0
        else:  # 'flat'
            threshold = 0.01  # 1% threshold for flat
            trade.correct = abs(trade.pnl_percent) < threshold
    
    def get_accuracy(self, window: Optional[int] = None) -> float:
        """
        Get prediction accuracy.
        
        Args:
            window: Number of recent trades to consider (None for all)
        
        Returns:
            Accuracy as percentage
        """
        closed_trades = [t for t in self.trades if t.correct is not None]
        
        if window:
            closed_trades = closed_trades[-window:]
        
        if not closed_trades:
            return 0.0
        
        correct = sum(1 for t in closed_trades if t.correct)
        return (correct / len(closed_trades)) * 100
    
    def get_win_rate(self, window: Optional[int] = None) -> float:
        """
        Get win rate (profitable trades).
        
        Args:
            window: Number of recent trades to consider
        
        Returns:
            Win rate as percentage
        """
        closed_trades = [t for t in self.trades if t.pnl is not None]
        
        if window:
            closed_trades = closed_trades[-window:]
        
        if not closed_trades:
            return 0.0
        
        wins = sum(1 for t in closed_trades if t.pnl > 0)
        return (wins / len(closed_trades)) * 100
    
    def get_total_pnl(self, window: Optional[int] = None) -> float:
        """
        Get total profit/loss.
        
        Args:
            window: Number of recent trades to consider
        
        Returns:
            Total PnL
        """
        closed_trades = [t for t in self.trades if t.pnl is not None]
        
        if window:
            closed_trades = closed_trades[-window:]
        
        if not closed_trades:
            return 0.0
        
        return sum(t.pnl for t in closed_trades)
    
    def get_average_pnl(self, window: Optional[int] = None) -> float:
        """
        Get average profit/loss per trade.
        
        Args:
            window: Number of recent trades to consider
        
        Returns:
            Average PnL
        """
        closed_trades = [t for t in self.trades if t.pnl is not None]
        
        if window:
            closed_trades = closed_trades[-window:]
        
        if not closed_trades:
            return 0.0
        
        return np.mean([t.pnl for t in closed_trades])
    
    def get_profit_factor(self, window: Optional[int] = None) -> float:
        """
        Get profit factor (gross profit / gross loss).
        
        Args:
            window: Number of recent trades to consider
        
        Returns:
            Profit factor
        """
        closed_trades = [t for t in self.trades if t.pnl is not None]
        
        if window:
            closed_trades = closed_trades[-window:]
        
        if not closed_trades:
            return 0.0
        
        gross_profit = sum(t.pnl for t in closed_trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in closed_trades if t.pnl < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def get_confidence_calibration(self) -> Dict[str, List]:
        """
        Analyze confidence calibration.
        
        Returns:
            Dictionary with confidence bins and actual accuracy
        """
        closed_trades = [t for t in self.trades if t.correct is not None]
        
        if not closed_trades:
            return {'bins': [], 'accuracy': [], 'count': []}
        
        # Create confidence bins
        bins = np.linspace(0, 1, 11)  # 10% bins
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        accuracy_by_bin = []
        count_by_bin = []
        
        for i in range(len(bins) - 1):
            trades_in_bin = [
                t for t in closed_trades
                if bins[i] <= t.confidence < bins[i+1]
            ]
            
            if trades_in_bin:
                accuracy = sum(1 for t in trades_in_bin if t.correct) / len(trades_in_bin)
                accuracy_by_bin.append(accuracy)
                count_by_bin.append(len(trades_in_bin))
            else:
                accuracy_by_bin.append(0.0)
                count_by_bin.append(0)
        
        return {
            'bins': bin_centers.tolist(),
            'accuracy': accuracy_by_bin,
            'count': count_by_bin
        }
    
    def get_summary(self, window: Optional[int] = None) -> Dict:
        """
        Get comprehensive performance summary.
        
        Args:
            window: Number of recent trades to consider
        
        Returns:
            Dictionary with performance metrics
        """
        closed_trades = [t for t in self.trades if t.pnl is not None]
        
        if window:
            closed_trades = closed_trades[-window:]
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'accuracy': 0.0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'profit_factor': 0.0
            }
        
        return {
            'total_trades': len(closed_trades),
            'accuracy': self.get_accuracy(window),
            'win_rate': self.get_win_rate(window),
            'total_pnl': self.get_total_pnl(window),
            'avg_pnl': self.get_average_pnl(window),
            'profit_factor': self.get_profit_factor(window),
            'avg_confidence': np.mean([t.confidence for t in closed_trades])
        }
