# tests/template_test.py
# Pytest-style template tests. Extend with your own indicator and equity checks.

from pathlib import Path
import csv
import pytest
import pandas as pd
import time
from fastapi.testclient import TestClient

from src.indicators import calculate_sma, calculate_rsi, determine_trend, make_decision
from src.signal import app

BASE = Path(__file__).resolve().parents[1]

# Fixtures
@pytest.fixture
def sample_prices():
    # Price data going up, then down
    return [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 109, 108, 107, 106, 105]

@pytest.fixture
def negative_prices():
    return [100, 101, -102, 103]

# Original Template Tests
def test_csv_has_expected_columns():
    csv_path = BASE / "ohlcv.csv"
    assert csv_path.exists(), "ohlcv.csv is missing"
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        headers = next(reader)
    for col in ["timestamp","open","high","low","close","volume"]:
        assert col in headers, f"Missing column: {col}"

def test_placeholder_equity_curve_reproducible():
    # TODO: Replace with a real check once your runner is implemented.
    assert True

# Indicator Tests
def test_calculate_sma(sample_prices):
    """Test SMA calculation."""
    sma_5 = calculate_sma(sample_prices[-5:], 5)
    assert sma_5 == pytest.approx(107.0)
    
    sma_10 = calculate_sma(sample_prices[-10:], 10)
    assert sma_10 == pytest.approx(107.5)

    # Test with insufficient data
    sma_insufficient = calculate_sma([100, 101], 5)
    assert pd.isna(sma_insufficient)

def test_calculate_rsi(sample_prices):
    """Test RSI calculation."""
    rsi_14 = calculate_rsi(sample_prices, 14)
    assert 0 <= rsi_14 <= 100
    
    # Test with insufficient data
    rsi_insufficient = calculate_rsi([100, 101], 14)
    assert pd.isna(rsi_insufficient)

def test_indicator_validation(negative_prices):
    """Test validation in indicator functions."""
    with pytest.raises(ValueError):
        calculate_sma(negative_prices, 4)
    with pytest.raises(ValueError):
        calculate_rsi(negative_prices, 4)

def test_determine_trend():
    """Test trend determination."""
    assert determine_trend(50, 48) == "UP"
    assert determine_trend(48, 50) == "DOWN"
    assert determine_trend(50, 50) == "FLAT"
    assert determine_trend(pd.NA, 50) == "FLAT"
    assert determine_trend(50, pd.NA) == "FLAT"

def test_make_decision():
    """Test trading decision logic."""
    # Uptrend
    assert make_decision(50, 48, 60) == "BUY"
    assert make_decision(50, 48, 80) == "HOLD" # Overbought

    # Downtrend
    assert make_decision(48, 50, 40) == "SELL"
    assert make_decision(48, 50, 20) == "HOLD" # Oversold

    # Flat trend
    assert make_decision(50, 50, 50) == "HOLD"
    
    # Insufficient data
    assert make_decision(pd.NA, 50, 50) == "HOLD"
    assert make_decision(50, pd.NA, 50) == "HOLD"
    assert make_decision(50, 48, pd.NA) == "HOLD"

# API Endpoint Test
def test_get_signal_endpoint():
    """Test the GET /signal endpoint."""
    with TestClient(app) as client:
        # Wait for the consumer to produce a signal
        time.sleep(1.0) # Increased wait time
        
        response = client.get("/signal?symbol=XYZ")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "symbol" in data
        assert data["symbol"] == "XYZ"
        assert "price" in data
        assert "trend" in data
        assert "rsi" in data
        assert "decision" in data
        assert "timestamp" in data

def test_get_signal_invalid_symbol():
    """Test the GET /signal endpoint with an invalid symbol."""
    with TestClient(app) as client:
        response = client.get("/signal?symbol=")
        assert response.status_code == 400
        
        response = client.get("/signal?symbol=INVALID")
        assert response.status_code == 404
