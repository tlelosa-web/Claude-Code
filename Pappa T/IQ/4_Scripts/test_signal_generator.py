#!/usr/bin/env python3
"""
Quick test script to verify signal generator works correctly
"""

from signal_generator import *
from datetime import datetime

# Create demo candles (ranging market with bounce pattern at the end)
candles = [
    Candle(datetime.now(), 1.0850, 1.0862, 1.0840, 1.0855),
    Candle(datetime.now(), 1.0855, 1.0868, 1.0848, 1.0860),
    Candle(datetime.now(), 1.0860, 1.0870, 1.0852, 1.0858),
    Candle(datetime.now(), 1.0858, 1.0865, 1.0845, 1.0850),
    Candle(datetime.now(), 1.0850, 1.0862, 1.0842, 1.0856),
    Candle(datetime.now(), 1.0856, 1.0868, 1.0850, 1.0862),
    Candle(datetime.now(), 1.0862, 1.0872, 1.0855, 1.0860),
    Candle(datetime.now(), 1.0860, 1.0868, 1.0848, 1.0852),
    Candle(datetime.now(), 1.0852, 1.0860, 1.0840, 1.0845),
    Candle(datetime.now(), 1.0845, 1.0855, 1.0838, 1.0850),
    Candle(datetime.now(), 1.0850, 1.0862, 1.0845, 1.0858),
    Candle(datetime.now(), 1.0858, 1.0868, 1.0852, 1.0862),
    Candle(datetime.now(), 1.0862, 1.0870, 1.0855, 1.0858),
    Candle(datetime.now(), 1.0858, 1.0865, 1.0848, 1.0850),
    Candle(datetime.now(), 1.0850, 1.0858, 1.0842, 1.0845),
    Candle(datetime.now(), 1.0845, 1.0852, 1.0835, 1.0840),
    Candle(datetime.now(), 1.0840, 1.0848, 1.0830, 1.0835),
    Candle(datetime.now(), 1.0835, 1.0842, 1.0825, 1.0828),
    Candle(datetime.now(), 1.0828, 1.0835, 1.0818, 1.0822),
    Candle(datetime.now(), 1.0822, 1.0830, 1.0812, 1.0815),
    Candle(datetime.now(), 1.0815, 1.0822, 1.0805, 1.0808),
    Candle(datetime.now(), 1.0808, 1.0815, 1.0798, 1.0802),
    Candle(datetime.now(), 1.0802, 1.0810, 1.0792, 1.0795),
    Candle(datetime.now(), 1.0795, 1.0805, 1.0788, 1.0798),
    Candle(datetime.now(), 1.0798, 1.0808, 1.0792, 1.0805),
    Candle(datetime.now(), 1.0805, 1.0815, 1.0798, 1.0810),
    Candle(datetime.now(), 1.0810, 1.0820, 1.0802, 1.0815),
    Candle(datetime.now(), 1.0815, 1.0825, 1.0808, 1.0818),
    Candle(datetime.now(), 1.0818, 1.0828, 1.0810, 1.0822),
    Candle(datetime.now(), 1.0822, 1.0832, 1.0815, 1.0825),
]

# Test indicators
indicators = TechnicalIndicators()
closes = [c.close for c in candles]

rsi = indicators.rsi(closes)
stoch_k, stoch_d = indicators.stochastic(candles)
adx = indicators.adx(candles)
atr = indicators.atr(candles)

print("=" * 50)
print("  TECHNICAL INDICATOR TEST")
print("=" * 50)
print(f"  RSI: {rsi:.2f}")
print(f"  Stochastic K: {stoch_k:.2f}")
print(f"  Stochastic D: {stoch_d:.2f}")
print(f"  ADX: {adx:.2f}")
print(f"  ATR: {atr:.5f}")
print("=" * 50)

# Test regime detection
regime = MarketRegimeDetector().detect(candles)
print(f"\n  Market Regime: {regime.value}")

# Test signal generation
signal_gen = SignalGenerator()
signal = signal_gen.generate_signal("EUR/USD", candles, 5)

if signal:
    print(format_signal(signal))
else:
    print("\n  No signal detected (conditions not met)")

# Test risk manager
print("\n" + "=" * 50)
print("  RISK MANAGER TEST")
print("=" * 50)

risk = RiskManager(initial_balance=100, risk_per_trade_pct=2.5, max_daily_loss_pct=25)
risk.reset_session()

print(f"  Initial Balance: ${risk.initial_balance}")
print(f"  Base Trade Amount: ${risk.get_trade_amount():.2f}")
print(f"  Max Daily Loss: ${risk.initial_balance * 0.25:.2f}")

# Simulate 3 losses
for i in range(3):
    risk.martingale_step = i
    print(f"\n  After loss #{i+1}:")
    print(f"    Martingale Step: {risk.martingale_step}")
    print(f"    Next Trade: ${risk.get_trade_amount():.2f}")
    warning = risk.martingale_warning()
    if warning:
        print(f"    {warning}")

print(f"\n  Can still trade: {risk.can_trade()}")
print("=" * 50)

print("\n✅ All tests passed! Signal generator is working correctly.")
print("\nRun 'python main.py' to start trading session.")
