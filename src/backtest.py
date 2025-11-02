# src/backtest.py

import pandas as pd
from pathlib import Path
from datetime import timezone

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Price, Quantity, Money
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.model.enums import OmsType, AccountType
from nautilus_trader.model.currencies import USD
from nautilus_trader.core.datetime import dt_to_unix_nanos, maybe_unix_nanos_to_dt

from src.indicators import calculate_sma, calculate_rsi, make_decision


class MovingAverageRSIStrategy(Strategy):
    def __init__(self, instrument, bar_type: BarType):
        super().__init__()
        self.instrument = instrument
        self.instrument_id = instrument.id
        self.bar_type = bar_type
        self.prices = []
        self.warm_up_period = 50  # For the longest MA lookback

    def on_start(self):
        self.subscribe_bars(self.bar_type)

    def is_last_bar_of_day(self, bar):
        dt = maybe_unix_nanos_to_dt(bar.ts_event)
        return dt.hour == 23 and dt.minute == 59

    def on_bar(self, bar: Bar):
        self.prices.append(float(bar.close))

        if len(self.prices) < self.warm_up_period:
            return

        if self.is_last_bar_of_day(bar):
            if self.portfolio.has_position(self.instrument_id):
                self.close_all_positions()
            return

        sma_20 = calculate_sma(self.prices, 20)
        sma_50 = calculate_sma(self.prices, 50)
        rsi_14 = calculate_rsi(self.prices, 14)

        decision = make_decision(sma_20, sma_50, rsi_14)
        net_position = self.portfolio.net_position(self.instrument_id)

        if decision == "BUY" and net_position == 0:
            self.buy(bar)
        elif decision == "SELL" and net_position != 0:
            self.sell(bar)

    def buy(self, bar: Bar):
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity.from_int(1),
            price=Price.from_str(str(bar.close)),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def sell(self, bar: Bar):
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=Quantity.from_int(1),
            price=Price.from_str(str(bar.close)),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def close_all_positions(self):
        for position in self.portfolio.open_positions():
            self.cancel_orders(position.instrument_id)
            self.close_position(position.instrument_id)


def run_backtest(data: pd.DataFrame, seed: int = 0):
    venue = Venue("SIM")
    instrument = TestInstrumentProvider.default_fx_ccy("XYZ/USD", venue)

    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id="BACKTESTER-001",
        )
    )

    engine.add_venue(
        venue,
        oms_type=OmsType.HEDGING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(1_000_000, USD)],
    )

    engine.add_instrument(instrument)

    bar_type = BarType.from_str("XYZ/USD.SIM-1-MINUTE-BID-EXTERNAL")
    bars = [
        Bar(
            bar_type=bar_type,
            ts_event=dt_to_unix_nanos(row["timestamp"]),
            ts_init=dt_to_unix_nanos(row["timestamp"]),
            # open=Price.from_str(str(row["open"])),
            # high=Price.from_str(str(row["high"])),
            # low=Price.from_str(str(row["low"])),
            # close=Price.from_str(str(row["close"])),
            open=Price.from_str(f"{row['open']:.{instrument.price_precision}f}"),
            high=Price.from_str(f"{row['high']:.{instrument.price_precision}f}"),
            low=Price.from_str(f"{row['low']:.{instrument.price_precision}f}"),
            close=Price.from_str(f"{row['close']:.{instrument.price_precision}f}"),
            volume=Quantity.from_int(row["volume"]),
        )
        for _, row in data.iterrows()
    ]
    engine.add_data(bars)

    strategy = MovingAverageRSIStrategy(instrument, bar_type)
    engine.add_strategy(strategy)

    start = data["timestamp"].min().to_pydatetime().replace(tzinfo=timezone.utc)
    end = data["timestamp"].max().to_pydatetime().replace(tzinfo=timezone.utc)

    result = engine.run(start=start, end=end)

    print("--- Backtest Results ---")
    print(f"Total PnL: {result.portfolio_pnl:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2f}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")

    return result


if __name__ == "__main__":
    data_path = Path(__file__).resolve().parents[1] / "ohlcv.csv"
    data = pd.read_csv(data_path)
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="s")

    run_backtest(data)
