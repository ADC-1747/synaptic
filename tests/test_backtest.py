# tests/test_backtest.py

import pandas as pd
from pathlib import Path
from src.backtest import run_backtest

def test_backtest_reproducibility():
    """
    Tests that the backtest produces the same equity curve for the same seed.
    """
    # Load data
    data_path = Path(__file__).resolve().parents[1] / "ohlcv.csv"
    data = pd.read_csv(data_path)
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="s")
    
    # Use a slice of the data for the test
    data_slice = data.head(200)

    # Run the backtest with a fixed seed
    result1 = run_backtest(data_slice, seed=123)
    equity_curve1 = result1.equity_curve

    # Run the backtest again with the same seed
    result2 = run_backtest(data_slice, seed=123)
    equity_curve2 = result2.equity_curve

    # Check that the equity curves are identical
    pd.testing.assert_frame_equal(equity_curve1, equity_curve2)
