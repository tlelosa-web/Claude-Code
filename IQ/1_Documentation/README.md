# 📊 IQ Option Signal Generator

A regime-filtered signal generator for IQ Option digital options trading. Designed to solve the #1 problem that blows accounts: **using the wrong strategy for the current market condition**.

---

## 🎯 What This Does

- **Detects Market Regime** - Uses ADX to determine if market is TRENDING or RANGING
- **Generates Signals** - RSI + Stochastic oversold/overbought conditions
- **Confidence Scoring** - Each signal gets a 0-100% confidence based on indicator confluence
- **Risk Management** - Daily loss tracking (25% hard stop), Martingale tracker (blocks at step 4+)
- **Signal Logging** - All signals saved to CSV for review and strategy analysis

---

## 🚀 Quick Start

### Requirements
- Python 3.7 or higher
- No external libraries needed (uses only standard library)

### Run the Signal Generator
```bash
python main.py
```

---

## 📖 How to Use

### 1. Start a Session
- Enter your **initial account balance**
- Set **risk per trade** (default 2.5%)
- Set **max daily loss** (default 25%)
- Choose **asset pair** (e.g., EUR/USD)
- Choose **expiry time** (1, 5, 10, or 15 minutes)

### 2. Enter Candle Data
- Enter **30 candles** of historical price data (oldest to newest)
- Format: `OPEN HIGH LOW CLOSE` (space or comma separated)
- Example: `1.0850 1.0865 1.0840 1.0845`
- Type `skip` during entry to load demo data for testing

### 3. Receive Signal
If conditions are met, you'll see:
```
==================================================
  📈 SIGNAL DETECTED
==================================================
  🟢 Asset:     EUR/USD
  🟢 Direction:  CALL
  ⏱️  Expiry:    5 min
  🎯 Confidence: 75.5%
  📊 Regime:    RANGING
  📉 RSI:       28.5
  📉 Stoch K/D: 15.2 / 18.3
  📊 ADX:       18.5
==================================================
```

### 4. Record Outcome
- After the trade closes, enter whether it **Won** or **Lost**
- The system tracks your daily P/L and enforces the 25% stop-loss

### 5. Review Session
- View session summary anytime (balance, win rate, trades count)
- All signals are logged to a CSV file (`signals_YYYYMMDD.csv`)

---

## 🧠 Strategy Logic

### Signal Generation
| Condition | CALL Signal | PUT Signal |
|-----------|-------------|------------|
| RSI | ≤ 30 (oversold) | ≥ 70 (overbought) |
| Stochastic | K ≤ 20 (oversold) | K ≥ 80 (overbought) |

### Confidence Scoring (0-100%)
- **Base confidence**: 50%
- **RSI extreme levels** (≤20 or ≥80): +15%
- **Stochastic K/D alignment**: +10%
- **Ranging market bonus**: +15%
- **Weak ADX (<20)**: +10%
- **TRENDING market penalty**: confidence × 0.5

### Regime Detection
| ADX Value | Market Regime |
|-----------|---------------|
| ≥ 25 | TRENDING |
| < 25 | RANGING |

**Key insight**: This strategy excels in RANGING markets. In TRENDING markets, confidence is halved to warn you that reversal signals are risky.

---

## 🛡️ Risk Management Rules

### Daily Loss Limit
- **Default**: 25% of initial balance
- **Action when hit**: Trading is BLOCKED until next session

### Martingale Tracker
| Step | Action |
|------|--------|
| 0-1 | Normal trading |
| 2 | ⚡ Warning: "Proceed with caution" |
| 3 | ⚠️ WARNING: "Consider stopping" |
| 4+ | 🛑 BLOCKED: Max steps reached |

### Trade Amount Calculation
- **Base amount**: Initial balance × risk% (e.g., $100 × 2.5% = $2.50)
- **Martingale**: Each loss doubles the next trade amount
- **Reset**: Martingale resets to step 0 after a win

---

## 📁 Output Files

### Signal Log (CSV)
File: `signals_YYYYMMDD.csv`

Columns:
- Timestamp
- Asset
- Direction (CALL/PUT)
- Expiry (minutes)
- Confidence %
- Regime (TRENDING/RANGING)
- RSI, Stoch K, Stoch D, ADX values
- Outcome (Won/Lost/Pending)
- Payout
- Martingale Step

**Use this file to review your strategy performance and identify what works.**

---

## ⚠️ Important Warnings

1. **This tool generates signals only** - you manually execute trades on IQ Option
2. **Past performance does not guarantee future results**
3. **Martingale is HIGH RISK** - use only if you understand the consequences
4. **Never risk money you cannot afford to lose**
5. **The 25% daily stop-loss is a HARD LIMIT** - respect it

---

## 🔧 Customization

You can modify these settings in `signal_generator.py`:

```python
# Oversold/Overbought thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
STOCH_OVERSOLD = 20
STOCH_OVERBOUGHT = 80

# Regime detection
ADX_THRESHOLD = 25.0  # Above = trending, below = ranging
```

---

## 📝 Session Workflow

```
1. Start Session → Enter balance, risk settings
2. Enter Candles → 30 candles of price data
3. Get Signal → CALL/PUT with confidence %
4. Execute Trade → Manually on IQ Option platform
5. Record Outcome → Won or Lost
6. Repeat → Until daily loss limit or you stop
7. Review → Check CSV log for strategy analysis
```

---

## 🐛 Troubleshooting

**Q: "Need at least 30 candles"**
A: You must enter 30 historical candles for accurate indicator calculation.

**Q: "No signal detected"**
A: Market conditions don't meet the criteria (RSI + Stochastic not in oversold/overbought zones). This is normal - not every moment is a good trading opportunity.

**Q: "Daily loss limit reached"**
A: You've hit the 25% stop-loss. End the session and review your strategy.

**Q: "Max martingale steps reached"**
A: You've lost 4 consecutive trades. This is a hard stop to prevent account blowup.

---

## 📞 Support

For questions or improvements, review the code in:
- `signal_generator.py` - Core logic (indicators, signals, risk management)
- `main.py` - CLI interface and session management

---

**Built for disciplined trading. Review your logs. Learn. Improve. Stay consistent.**
