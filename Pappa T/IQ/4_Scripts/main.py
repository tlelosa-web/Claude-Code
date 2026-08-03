#!/usr/bin/env python3
"""
IQ Option Signal Generator - Main CLI Interface
Interactive menu for managing trading sessions with live market data or manual candle entry.
Supports regime-filtered signals, risk management, and signal logging.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path when running from 4_Scripts/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signal_generator import (
    Candle, SignalGenerator, RiskManager, SignalLogger,
    SignalDirection, MarketRegime, format_signal, _debug_log
)
from live_data_feed import fetch_live_candles


# ============================================================
# HEADER AND SETUP
# ============================================================
def print_header():
    """Print application header"""
    print("\n" + "=" * 60)
    print("  📊 IQ OPTION SIGNAL GENERATOR")
    print("  Live Market Data | Regime-Filtered | Risk Managed")
    print("=" * 60)


def get_initial_balance() -> float:
    """Prompt user for initial account balance"""
    while True:
        try:
            balance = float(input("\n💰 Enter your initial account balance ($): "))
            if balance <= 0:
                print("   ❌ Balance must be greater than 0")
                continue
            return balance
        except ValueError:
            print("   ❌ Please enter a valid number")


def get_risk_settings() -> tuple:
    """Get risk settings from user"""
    print("\n⚙️  Risk Settings (defaults in brackets)")

    while True:
        try:
            risk_pct = input("   Risk per trade % [2.5]: ").strip()
            risk_pct = float(risk_pct) if risk_pct else 2.5
            if risk_pct <= 0 or risk_pct > 10:
                print("   ⚠️  Risk should be between 0.5% and 10%")
                continue
            break
        except ValueError:
            print("   ❌ Invalid number")

    while True:
        try:
            max_loss_pct = input("   Max daily loss % [25]: ").strip()
            max_loss_pct = float(max_loss_pct) if max_loss_pct else 25
            if max_loss_pct <= 0 or max_loss_pct > 50:
                print("   ⚠️  Max loss should be between 5% and 50%")
                continue
            break
        except ValueError:
            print("   ❌ Invalid number")

    return risk_pct, max_loss_pct


def get_asset() -> str:
    """Get asset pair from user"""
    valid_pairs = [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
        "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY",
        "CAD/JPY", "CHF/JPY", "EUR/AUD", "EUR/CAD", "GBP/AUD",
        "GBP/CAD", "USD/CHF", "AUD/CAD", "AUD/NZD", "EUR/NZD"
    ]

    while True:
        asset = input("\n💱 Enter asset pair (e.g., EUR/USD): ").strip()
        # Normalize format
        if "/" in asset:
            parts = asset.split("/")
            asset = f"{parts[0].strip()}/{parts[1].strip()}"
        asset_upper = asset.upper()
        if asset_upper in valid_pairs:
            return asset_upper
        print(f"   ⚠️  Common pairs: {', '.join(valid_pairs[:5])}")
        confirm = input(f"   Use '{asset_upper}' anyway? (y/n): ").strip().lower()
        if confirm == 'y':
            return asset_upper


def get_expiry() -> int:
    """Get expiry time in minutes"""
    print("\n⏱️  Expiry time:")
    print("   1. 1 minute")
    print("   2. 5 minutes (recommended)")
    print("   3. 10 minutes")
    print("   4. 15 minutes")
    print("   5. Custom")

    while True:
        try:
            choice = input("   Select [2]: ").strip()
            choice = choice if choice else "2"
            expiry_map = {"1": 1, "2": 5, "3": 10, "4": 15}
            if choice in expiry_map:
                return expiry_map[choice]
            if choice == "5":
                mins = int(input("   Enter custom minutes (1-15): ").strip())
                if 1 <= mins <= 15:
                    return mins
                print("   ❌ Must be between 1 and 15")
            else:
                print("   ❌ Invalid choice")
        except ValueError:
            print("   ❌ Please enter a number")


def get_interval() -> int:
    """Get candle interval in minutes for live data"""
    print("\n📏 Candle interval:")
    print("   1. 1 minute")
    print("   2. 5 minutes")
    print("   3. 15 minutes")

    while True:
        try:
            choice = input("   Select [1]: ").strip()
            choice = choice if choice else "1"
            interval_map = {"1": 1, "2": 5, "3": 15}
            if choice in interval_map:
                return interval_map[choice]
            print("   ❌ Invalid choice")
        except ValueError:
            print("   ❌ Please enter a number")


# ============================================================
# CANDLE DATA SOURCES
# ============================================================
def enter_candles(count: int = 30) -> list:
    """Manual candle entry"""
    print(f"\n📊 Enter {count} candles (oldest to newest)")
    print("   Format: OPEN HIGH LOW CLOSE (comma or space separated)")
    print("   Type 'skip' to load demo data for testing\n")

    candles = []

    for i in range(count):
        while True:
            try:
                entry = input(f"   Candle {i+1}/{count}: ").strip()

                if entry.lower() == 'skip':
                    return None  # Signal to use demo data

                parts = entry.replace(',', ' ').split()
                if len(parts) != 4:
                    print("   ❌ Need exactly 4 values: Open High Low Close")
                    continue

                open_p, high, low, close = map(float, parts)

                if high < max(open_p, close) or low > min(open_p, close):
                    print("   ❌ High must be >= Open/Close, Low must be <= Open/Close")
                    continue

                candle = Candle(
                    timestamp=datetime.now(),
                    open=open_p,
                    high=high,
                    low=low,
                    close=close
                )
                candles.append(candle)
                break

            except ValueError:
                print("   ❌ Invalid numbers. Use format: Open High Low Close")

    return candles


def load_demo_candles() -> list:
    """Load sample candle data for testing"""
    demo_data = [
        Candle(datetime.now(), 1.0850, 1.0865, 1.0840, 1.0845),
        Candle(datetime.now(), 1.0845, 1.0855, 1.0835, 1.0850),
        Candle(datetime.now(), 1.0850, 1.0860, 1.0842, 1.0858),
        Candle(datetime.now(), 1.0858, 1.0870, 1.0850, 1.0852),
        Candle(datetime.now(), 1.0852, 1.0862, 1.0845, 1.0848),
        Candle(datetime.now(), 1.0848, 1.0858, 1.0840, 1.0842),
        Candle(datetime.now(), 1.0842, 1.0852, 1.0835, 1.0838),
        Candle(datetime.now(), 1.0838, 1.0848, 1.0830, 1.0835),
        Candle(datetime.now(), 1.0835, 1.0845, 1.0825, 1.0828),
        Candle(datetime.now(), 1.0828, 1.0838, 1.0820, 1.0822),
        Candle(datetime.now(), 1.0822, 1.0832, 1.0815, 1.0818),
        Candle(datetime.now(), 1.0818, 1.0828, 1.0810, 1.0812),
        Candle(datetime.now(), 1.0812, 1.0822, 1.0805, 1.0808),
        Candle(datetime.now(), 1.0808, 1.0818, 1.0800, 1.0805),
        Candle(datetime.now(), 1.0805, 1.0815, 1.0798, 1.0802),
        Candle(datetime.now(), 1.0802, 1.0812, 1.0795, 1.0800),
        Candle(datetime.now(), 1.0800, 1.0810, 1.0792, 1.0798),
        Candle(datetime.now(), 1.0798, 1.0808, 1.0790, 1.0795),
        Candle(datetime.now(), 1.0795, 1.0805, 1.0788, 1.0792),
        Candle(datetime.now(), 1.0792, 1.0802, 1.0785, 1.0788),
        Candle(datetime.now(), 1.0788, 1.0798, 1.0780, 1.0785),
        Candle(datetime.now(), 1.0785, 1.0795, 1.0778, 1.0782),
        Candle(datetime.now(), 1.0782, 1.0792, 1.0775, 1.0780),
        Candle(datetime.now(), 1.0780, 1.0790, 1.0773, 1.0778),
        Candle(datetime.now(), 1.0778, 1.0788, 1.0770, 1.0775),
        Candle(datetime.now(), 1.0775, 1.0785, 1.0768, 1.0772),
        Candle(datetime.now(), 1.0772, 1.0782, 1.0765, 1.0770),
        Candle(datetime.now(), 1.0770, 1.0780, 1.0762, 1.0768),
        Candle(datetime.now(), 1.0768, 1.0778, 1.0760, 1.0765),
        Candle(datetime.now(), 1.0765, 1.0775, 1.0758, 1.0762),
    ]
    return demo_data


# ============================================================
# RISK AND TRADE MANAGEMENT
# ============================================================
def display_risk_status(risk_manager: RiskManager):
    """Display current risk status"""
    loss_pct = risk_manager.daily_loss_percentage()
    print(f"\n📊 Risk Status:")
    print(f"   Balance: ${risk_manager.current_balance:.2f} / ${risk_manager.initial_balance:.2f}")
    print(f"   Daily Loss: {loss_pct:.1f}% / {risk_manager.max_daily_loss_pct}%")
    print(f"   Martingale Step: {risk_manager.martingale_step}/{risk_manager.max_martingale_steps}")
    print(f"   Next Trade Amount: ${risk_manager.get_trade_amount():.2f}")

    warning = risk_manager.martingale_warning()
    if warning:
        print(f"   {warning}")

    if not risk_manager.can_trade():
        print(f"\n   🛑 DAILY LOSS LIMIT REACHED. STOP TRADING.")
    if risk_manager.should_block_martingale():
        print(f"   🛑 MAX MARTINGALE STEPS REACHED. STOP TRADING.")


def record_trade_outcome(signal, risk_manager: RiskManager, logger: SignalLogger):
    """Record whether a trade won or lost"""
    while True:
        outcome = input(f"\n📝 Trade outcome for {signal.asset} {signal.direction.value}? (w/n): ").strip().lower()
        if outcome in ['w', 'won', 'win']:
            payout_pct = float(input("   Payout % (e.g., 85 for 85% return): ") or "85")
            payout = risk_manager.get_trade_amount() * (payout_pct / 100)
            risk_manager.record_trade(signal, won=True, payout=payout)
            logger.log_signal(signal, won=True, payout=payout, martingale_step=risk_manager.martingale_step)
            print(f"   ✅ Won! +${payout:.2f}")
            break
        elif outcome in ['n', 'no', 'lost', 'loss']:
            risk_manager.record_trade(signal, won=False)
            logger.log_signal(signal, won=False, martingale_step=risk_manager.martingale_step)
            loss = risk_manager.get_trade_amount()
            print(f"   ❌ Lost! -${loss:.2f}")
            break
        else:
            print("   ❌ Enter 'w' for win or 'n' for loss")


# ============================================================
# TRADING SESSION
# ============================================================
def trading_session():
    """Main trading session loop with live data support"""
    print_header()

    # Setup
    balance = get_initial_balance()
    risk_pct, max_loss_pct = get_risk_settings()

    risk_manager = RiskManager(
        initial_balance=balance,
        risk_per_trade_pct=risk_pct,
        max_daily_loss_pct=max_loss_pct
    )
    risk_manager.reset_session()

    signal_gen = SignalGenerator()
    logger = SignalLogger()

    asset = get_asset()
    expiry = get_expiry()

    _debug_log(f"SESSION START: Balance=${balance}, Asset={asset}, Expiry={expiry}min, Risk={risk_pct}%")

    print(f"\n{'='*60}")
    print(f"  Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Asset: {asset} | Expiry: {expiry}min | Risk: {risk_pct}%")
    print(f"  Max Daily Loss: {max_loss_pct}% (${balance * max_loss_pct/100:.2f})")
    print(f"{'='*60}")

    # Cache for candles from previous fetch
    cached_candles = None

    # Main loop
    while True:
        display_risk_status(risk_manager)

        # Check if trading is blocked
        if not risk_manager.can_trade():
            print("\n🛑 DAILY LOSS LIMIT REACHED. END SESSION.")
            _debug_log("SESSION END: Daily loss limit reached")
            break
        if risk_manager.should_block_martingale():
            print("\n🛑 MAX MARTINGALE STEPS REACHED. END SESSION.")
            _debug_log("SESSION END: Max martingale steps reached")
            break

        print(f"\n{'='*40}")
        print("  MENU:")
        print("  1. 📡 Fetch LIVE data and get signal")
        print("  2. 📝 Enter candles manually")
        print("  3. 🔄 Refresh signal (use latest live data)")
        print("  4. 📊 Record trade outcome")
        print("  5. 📋 View session summary")
        print("  6. 🚪 End session")
        print(f"{'='*40}")

        choice = input("\nSelect action [1-6]: ").strip()

        if choice == '1':
            # === LIVE DATA MODE ===
            interval = get_interval()
            candles = fetch_live_candles(asset, interval_minutes=interval, count=30)

            if candles is None:
                print("\n   ❌ Failed to fetch live data.")
                print("   Check internet connection or install yfinance: pip install yfinance")
                _debug_log("LIVE DATA FAILED: Could not fetch data for {asset}")
                continue

            cached_candles = candles
            _debug_log(f"LIVE DATA: {asset} — {len(candles)} candles fetched ({interval}m interval)")

            # Generate signal
            signal = signal_gen.generate_signal(asset, candles, expiry)

            if signal:
                print(format_signal(signal))
                logger.log_signal(signal)

                took = input("Did you take this trade? (y/n): ").strip().lower()
                if took == 'y':
                    record_trade_outcome(signal, risk_manager, logger)
            else:
                print("\n📊 No signal detected.")
                print("   Market conditions don't meet criteria (RSI + Stochastic not in zone).")
                _debug_log("NO SIGNAL: Conditions not met for {asset}")

        elif choice == '2':
            # === MANUAL MODE ===
            candles = enter_candles()

            if candles is None:
                print("\n⚠️  Loading demo data for testing...")
                candles = load_demo_candles()
                _debug_log("DEMO DATA: Loaded for testing")

            if len(candles) < 30:
                print("❌ Need at least 30 candles for accurate signals")
                continue

            cached_candles = candles

            # Generate signal
            signal = signal_gen.generate_signal(asset, candles, expiry)

            if signal:
                print(format_signal(signal))
                logger.log_signal(signal)

                took = input("Did you take this trade? (y/n): ").strip().lower()
                if took == 'y':
                    record_trade_outcome(signal, risk_manager, logger)
            else:
                print("\n📊 No signal detected.")
                print("   Market conditions don't meet criteria.")

        elif choice == '3':
            # === REFRESH LIVE SIGNAL ===
            if cached_candles is None:
                print("⚠️  No live data cached. Use option 1 first.")
                continue

            interval = get_interval()
            candles = fetch_live_candles(asset, interval_minutes=interval, count=30)

            if candles is None:
                print("\n   ❌ Failed to refresh live data.")
                continue

            cached_candles = candles
            _debug_log(f"LIVE REFRESH: {asset} — {len(candles)} candles ({interval}m)")

            signal = signal_gen.generate_signal(asset, candles, expiry)

            if signal:
                print(format_signal(signal))
                logger.log_signal(signal)

                took = input("Did you take this trade? (y/n): ").strip().lower()
                if took == 'y':
                    record_trade_outcome(signal, risk_manager, logger)
            else:
                print("\n📊 No signal detected after refresh.")

        elif choice == '4':
            # === RECORD OUTCOME ===
            print("⚠️  Record outcome for the last signal.")
            print("   This works after taking a trade from option 1 or 2.")
            # In practice, outcome is recorded immediately after trade in options 1/2
            print("   (Outcomes are recorded automatically when you take a trade)")

        elif choice == '5':
            # === SESSION SUMMARY ===
            print(f"\n{'='*50}")
            print("  📊 SESSION SUMMARY")
            print(f"{'='*50}")
            print(f"  Initial Balance: ${risk_manager.initial_balance:.2f}")
            print(f"  Current Balance: ${risk_manager.current_balance:.2f}")
            print(f"  P/L: ${risk_manager.current_balance - risk_manager.initial_balance:+.2f}")
            print(f"  Daily Loss: {risk_manager.daily_loss_percentage():.1f}%")
            print(f"  Total Trades: {len(risk_manager.trades_today)}")

            wins = sum(1 for t in risk_manager.trades_today if t['won'])
            losses = sum(1 for t in risk_manager.trades_today if not t['won'])
            if len(risk_manager.trades_today) > 0:
                win_rate = (wins / len(risk_manager.trades_today)) * 100
                print(f"  Wins: {wins} | Losses: {losses} | Win Rate: {win_rate:.1f}%")
            print(f"{'='*50}")
            _debug_log("SESSION SUMMARY VIEWED")

        elif choice == '6':
            # === END SESSION ===
            confirm = input("End session? (y/n): ").strip().lower()
            if confirm == 'y':
                print(f"\n👋 Session ended.")
                print(f"   📁 Signal log: {logger.filename}")
                print(f"   📝 Debug log: 5_Archive_and_Debug/debug_log.txt")
                _debug_log(f"SESSION END: User exited. Log saved to {logger.filename}")
                break

        else:
            print("❌ Invalid choice. Enter 1-6.")


if __name__ == "__main__":
    try:
        trading_session()
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted. Exiting...")
        _debug_log("SESSION INTERRUPTED: User pressed Ctrl+C")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        _debug_log(f"SESSION ERROR: {e}")
        sys.exit(1)
