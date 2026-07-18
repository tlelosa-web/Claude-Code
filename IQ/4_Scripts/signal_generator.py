#!/usr/bin/env python3
"""
IQ Option Signal Generator
- Detects market regime (Trending vs Ranging)
- Generates CALL/PUT signals based on RSI + Stochastic oversold/overbought
- Confidence scoring based on indicator confluence + regime match
- Daily loss tracking with 25% hard stop
- Martingale step tracker with warnings
- Signal logging to CSV
"""

import math
import csv
import os
import sys
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ============================================================
# PROJECT PATH RESOLUTION
# ============================================================
def _get_project_root() -> str:
    """Resolve project root directory (handles flat or AGENT.md folder structure)."""
    current = os.path.dirname(os.path.abspath(__file__))
    # If we're in 4_Scripts/, go up one level
    if current.endswith("4_Scripts"):
        return os.path.dirname(current)
    # Otherwise assume we're already at project root
    return current


PROJECT_ROOT = _get_project_root()
REPORTS_DIR = os.path.join(PROJECT_ROOT, "3_Live_Reports")
DEBUG_LOG_DIR = os.path.join(PROJECT_ROOT, "5_Archive_and_Debug")

# Ensure output directories exist
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DEBUG_LOG_DIR, exist_ok=True)


# ============================================================
# DEBUG LOGGING HELPER
# ============================================================
DEBUG_LOG_FILE = os.path.join(DEBUG_LOG_DIR, "debug_log.txt")


def _debug_log(message: str):
    """Append timestamped message to debug log. Newest entries at top."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} — {message}"

        existing = ""
        if os.path.exists(DEBUG_LOG_FILE):
            with open(DEBUG_LOG_FILE, "r") as f:
                existing = f.read()

        with open(DEBUG_LOG_FILE, "w") as f:
            f.write(f"{log_entry}\n{existing}")
    except Exception:
        pass  # Never crash on logging failure


class SignalDirection(Enum):
    CALL = "CALL"
    PUT = "PUT"


class MarketRegime(Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    UNKNOWN = "UNKNOWN"


@dataclass
class Candle:
    """Represents a single candlestick"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class Signal:
    """Represents a trading signal"""
    asset: str
    direction: SignalDirection
    expiry_minutes: int
    confidence: float  # 0-100
    regime: MarketRegime
    rsi_value: float
    stoch_k: float
    stoch_d: float
    adx_value: float
    timestamp: datetime = field(default_factory=datetime.now)


class TechnicalIndicators:
    """Calculate technical indicators from price data"""

    @staticmethod
    def sma(data: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(data) < period:
            return []
        result = []
        for i in range(period - 1, len(data)):
            avg = sum(data[i - period + 1:i + 1]) / period
            result.append(avg)
        return result

    @staticmethod
    def ema(data: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(data) < period:
            return []
        multiplier = 2 / (period + 1)
        result = [sum(data[:period]) / period]
        for i in range(period, len(data)):
            ema_value = (data[i] - result[-1]) * multiplier + result[-1]
            result.append(ema_value)
        return result

    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> Optional[float]:
        """Relative Strength Index - returns latest value (Wilder's smoothing)"""
        if len(closes) < period + 1:
            return None

        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            gains.append(max(0, change))
            losses.append(max(0, -change))

        # Use Wilder's smoothing method (like standard RSI)
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        # Smooth with remaining data
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi_value = 100 - (100 / (1 + rs))
        return rsi_value

    @staticmethod
    def stochastic(candles: List[Candle], k_period: int = 14, d_period: int = 3) -> tuple:
        """Stochastic Oscillator - returns (K, D) latest values"""
        if len(candles) < k_period + d_period - 1:
            return None, None

        k_values = []
        for i in range(k_period - 1, len(candles)):
            recent = candles[i - k_period + 1:i + 1]
            highest_high = max(c.high for c in recent)
            lowest_low = min(c.low for c in recent)

            if highest_high == lowest_low:
                k_values.append(50.0)
            else:
                k = ((candles[i].close - lowest_low) / (highest_high - lowest_low)) * 100
                k_values.append(k)

        if len(k_values) < d_period:
            return k_values[-1] if k_values else None, None

        d_value = sum(k_values[-d_period:]) / d_period
        return k_values[-1], d_value

    @staticmethod
    def adx(candles: List[Candle], period: int = 14) -> Optional[float]:
        """Average Directional Index - returns latest value (proper Wilder's method)"""
        if len(candles) < period * 2 + 1:
            return None

        plus_dm = []
        minus_dm = []

        for i in range(1, len(candles)):
            high_diff = candles[i].high - candles[i - 1].high
            low_diff = candles[i - 1].low - candles[i].low

            if high_diff > low_diff and high_diff > 0:
                plus_dm.append(high_diff)
            else:
                plus_dm.append(0)

            if low_diff > high_diff and low_diff > 0:
                minus_dm.append(low_diff)
            else:
                minus_dm.append(0)

        # True Range
        tr_values = []
        for i in range(1, len(candles)):
            high_low = candles[i].high - candles[i].low
            high_close = abs(candles[i].high - candles[i - 1].close)
            low_close = abs(candles[i].low - candles[i - 1].close)
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)

        # Wilder's smoothing for TR, +DM, -DM
        atr = sum(tr_values[:period]) / period
        smoothed_plus = sum(plus_dm[:period]) / period
        smoothed_minus = sum(minus_dm[:period]) / period

        for i in range(period, len(tr_values)):
            atr = (atr * (period - 1) + tr_values[i]) / period
            smoothed_plus = (smoothed_plus * (period - 1) + plus_dm[i]) / period
            smoothed_minus = (smoothed_minus * (period - 1) + minus_dm[i]) / period

        if atr == 0:
            return None

        plus_di = (smoothed_plus / atr) * 100
        minus_di = (smoothed_minus / atr) * 100

        if (plus_di + minus_di) == 0:
            return 0

        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
        
        # For a single DX value, return the current DX
        return dx

    @staticmethod
    def atr(candles: List[Candle], period: int = 14) -> Optional[float]:
        """Average True Range"""
        if len(candles) < period + 1:
            return None

        tr_values = []
        for i in range(1, len(candles)):
            high_low = candles[i].high - candles[i].low
            high_close = abs(candles[i].high - candles[i - 1].close)
            low_close = abs(candles[i].low - candles[i - 1].close)
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)

        return sum(tr_values[-period:]) / period


class MarketRegimeDetector:
    """Detects if market is trending or ranging"""

    @staticmethod
    def detect(candles: List[Candle], adx_threshold: float = 25.0) -> MarketRegime:
        adx = TechnicalIndicators.adx(candles)
        if adx is None:
            return MarketRegime.UNKNOWN

        if adx >= adx_threshold:
            return MarketRegime.TRENDING
        else:
            return MarketRegime.RANGING


class SignalGenerator:
    """Main signal generator with regime filtering and confidence scoring"""

    # Oversold/Overbought thresholds
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    STOVERSOLD = 20
    STOVERBOUGHT = 80

    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.regime_detector = MarketRegimeDetector()

    def generate_signal(
        self,
        asset: str,
        candles: List[Candle],
        expiry_minutes: int = 5
    ) -> Optional[Signal]:
        """Generate a trading signal based on current market conditions"""

        if len(candles) < 30:
            return None

        closes = [c.close for c in candles]

        # Get indicator values
        rsi = self.indicators.rsi(closes)
        stoch_k, stoch_d = self.indicators.stochastic(candles)
        adx = self.indicators.adx(candles)

        if rsi is None or stoch_k is None or stoch_d is None or adx is None:
            return None

        # Detect regime
        regime = self.regime_detector.detect(candles)

        # Determine signal direction and confidence
        direction = None
        confidence = 0.0

        # CALL conditions (oversold reversal)
        if rsi <= self.RSI_OVERSOLD and stoch_k <= self.STOVERSOLD:
            direction = SignalDirection.CALL
            confidence = self._calculate_confidence(
                rsi, stoch_k, stoch_d, adx, regime, direction
            )

        # PUT conditions (overbought reversal)
        elif rsi >= self.RSI_OVERBOUGHT and stoch_k >= self.STOVERBOUGHT:
            direction = SignalDirection.PUT
            confidence = self._calculate_confidence(
                rsi, stoch_k, stoch_d, adx, regime, direction
            )

        if direction is None:
            return None

        # Filter by regime - only signal when regime matches strategy
        # This strategy works best in RANGING markets
        if regime == MarketRegime.TRENDING:
            confidence *= 0.5  # Reduce confidence in trending markets

        if confidence < 50:
            return None

        return Signal(
            asset=asset,
            direction=direction,
            expiry_minutes=expiry_minutes,
            confidence=round(confidence, 1),
            regime=regime,
            rsi_value=round(rsi, 2),
            stoch_k=round(stoch_k, 2),
            stoch_d=round(stoch_d, 2),
            adx_value=round(adx, 2)
        )

    def _calculate_confidence(
        self,
        rsi: float,
        stoch_k: float,
        stoch_d: float,
        adx: float,
        regime: MarketRegime,
        direction: SignalDirection
    ) -> float:
        """Calculate confidence score (0-100) based on indicator confluence"""
        confidence = 50  # Base confidence

        # RSI extreme bonus/penalty
        if direction == SignalDirection.CALL:
            if rsi <= 20:
                confidence += 15
            elif rsi <= 25:
                confidence += 10
            elif rsi <= 30:
                confidence += 5
        else:  # PUT
            if rsi >= 80:
                confidence += 15
            elif rsi >= 75:
                confidence += 10
            elif rsi >= 70:
                confidence += 5

        # Stochastic confluence
        k_d_diff = abs(stoch_k - stoch_d)
        if k_d_diff < 5:  # K and D are close (confirmation)
            confidence += 10
        elif k_d_diff < 10:
            confidence += 5

        # Stochastic extreme levels
        if direction == SignalDirection.CALL and stoch_k <= 10:
            confidence += 10
        elif direction == SignalDirection.PUT and stoch_k >= 90:
            confidence += 10

        # Regime bonus
        if regime == MarketRegime.RANGING:
            confidence += 15  # This strategy excels in ranging markets

        # ADX consideration
        if adx < 20:  # Weak trend = good for reversal
            confidence += 10
        elif adx < 25:
            confidence += 5

        return min(confidence, 100)


class RiskManager:
    """Manages risk, daily limits, and martingale tracking"""

    def __init__(self, initial_balance: float, risk_per_trade_pct: float = 2.5, max_daily_loss_pct: float = 25.0):
        self.initial_balance = initial_balance
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.current_balance = initial_balance
        self.martingale_step = 0
        self.max_martingale_steps = 4
        self.trades_today = []
        self.session_active = False
        self.session_start = None

    def can_trade(self) -> bool:
        """Check if trading is allowed based on daily loss limit"""
        daily_loss = self.initial_balance - self.current_balance
        max_loss = self.initial_balance * (self.max_daily_loss_pct / 100)

        if daily_loss >= max_loss:
            return False
        return True

    def daily_loss_percentage(self) -> float:
        """Calculate current daily loss percentage"""
        loss = self.initial_balance - self.current_balance
        if loss <= 0:
            return 0
        return (loss / self.initial_balance) * 100

    def record_trade(self, signal: Signal, won: bool, payout: float = 0):
        """Record a trade outcome"""
        self.trades_today.append({
            "timestamp": signal.timestamp,
            "asset": signal.asset,
            "direction": signal.direction.value,
            "won": won,
            "payout": payout,
            "martingale_step": self.martingale_step
        })

        if won:
            self.current_balance += payout
            self.martingale_step = 0  # Reset martingale on win
        else:
            self.current_balance -= self._trade_amount()

        if not won:
            self.martingale_step += 1

    def _trade_amount(self) -> float:
        """Calculate trade amount based on martingale step"""
        base_amount = self.initial_balance * (self.risk_per_trade_pct / 100)
        if self.martingale_step == 0:
            return base_amount
        return base_amount * (2 ** self.martingale_step)

    def martingale_warning(self) -> Optional[str]:
        """Return warning message if martingale step is high"""
        if self.martingale_step >= 3:
            return f"⚠️  WARNING: Martingale step {self.martingale_step}. Consider stopping."
        if self.martingale_step >= 2:
            return f"⚡ Martingale step {self.martingale_step}. Proceed with caution."
        return None

    def should_block_martingale(self) -> bool:
        """Block trading if max martingale steps reached"""
        return self.martingale_step >= self.max_martingale_steps

    def get_trade_amount(self) -> float:
        """Get the recommended trade amount"""
        return self._trade_amount()

    def reset_session(self):
        """Reset for a new trading session"""
        self.session_active = True
        self.session_start = datetime.now()
        self.martingale_step = 0
        self.trades_today = []


class SignalLogger:
    """Logs signals and trades to CSV in 3_Live_Reports/"""

    def __init__(self, filename: str = None):
        if filename is None:
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"signals_{date_str}.csv"
        # Save to 3_Live_Reports directory
        self.filename = os.path.join(REPORTS_DIR, filename)
        self._ensure_header()

    def _ensure_header(self):
        """Create CSV with header if it doesn't exist"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Asset", "Direction", "Expiry (min)",
                    "Confidence", "Regime", "RSI", "Stoch K", "Stoch D",
                    "ADX", "Outcome (Won/Lost)", "Payout", "Martingale Step"
                ])
            _debug_log(f"Signal log created: {self.filename}")

    def log_signal(self, signal: Signal, won: bool = None, payout: float = 0, martingale_step: int = 0):
        """Log a signal to CSV"""
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                signal.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                signal.asset,
                signal.direction.value,
                signal.expiry_minutes,
                signal.confidence,
                signal.regime.value,
                signal.rsi_value,
                signal.stoch_k,
                signal.stoch_d,
                signal.adx_value,
                "Won" if won else "Lost" if won is not None else "Pending",
                payout,
                martingale_step
            ])
        _debug_log(
            f"SIGNAL LOGGED: {signal.asset} {signal.direction.value} | "
            f"Confidence: {signal.confidence}% | Regime: {signal.regime.value} | "
            f"Outcome: {'Won' if won else 'Lost' if won is not None else 'Pending'}"
        )


def format_signal(signal: Signal) -> str:
    """Format signal for console output"""
    direction_color = "🟢" if signal.direction == SignalDirection.CALL else "🔴"
    return (
        f"\n{'='*50}\n"
        f"  📈 SIGNAL DETECTED\n"
        f"{'='*50}\n"
        f"  {direction_color} Asset:     {signal.asset}\n"
        f"  {direction_color} Direction:  {signal.direction.value}\n"
        f"  ⏱️  Expiry:    {signal.expiry_minutes} min\n"
        f"  🎯 Confidence: {signal.confidence}%\n"
        f"  📊 Regime:    {signal.regime.value}\n"
        f"  📉 RSI:       {signal.rsi_value}\n"
        f"  📉 Stoch K/D: {signal.stoch_k} / {signal.stoch_d}\n"
        f"  📊 ADX:       {signal.adx_value}\n"
        f"{'='*50}\n"
    )


if __name__ == "__main__":
    print("IQ Option Signal Generator loaded successfully.")
    print("Run 'main.py' to start the trading session.")
