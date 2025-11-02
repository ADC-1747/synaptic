# src/indicators.py

from typing import List
import pandas as pd
import numpy as np
from ta.momentum import rsi
from ta.trend import sma_indicator

def calculate_sma(prices: List[float], window: int) -> float:
    """Calculates the Simple Moving Average (SMA) for a list of prices."""
    if not prices or window <= 0 or len(prices) < window:
        return np.nan
    if any(p < 0 for p in prices):
        raise ValueError("Prices must be non-negative.")
    series = pd.Series(prices)
    sma = sma_indicator(series, window=window)
    return sma.iloc[-1]

def calculate_rsi(prices: List[float], window: int = 14) -> float:
    """Calculates the Relative Strength Index (RSI) for a list of prices."""
    if not prices or window <= 0 or len(prices) < window:
        return np.nan
    if any(p < 0 for p in prices):
        raise ValueError("Prices must be non-negative.")
    series = pd.Series(prices)
    rsi_values = rsi(series, window=window)
    return rsi_values.iloc[-1]

def determine_trend(sma_short: float, sma_long: float) -> str:
    """Determines the trend based on short and long SMAs."""
    if pd.isna(sma_short) or pd.isna(sma_long) or sma_short < 0 or sma_long < 0:
        return "FLAT"
    if sma_short > sma_long:
        return "UP"
    elif sma_short < sma_long:
        return "DOWN"
    else:
        return "FLAT"

def make_decision(sma_short: float, sma_long: float, rsi_value: float) -> str:
    """Makes a trading decision based on SMAs and RSI."""
    trend = determine_trend(sma_short, sma_long)
    
    if pd.isna(rsi_value) or not (0 <= rsi_value <= 100):
        return "HOLD"

    if trend == "UP" and rsi_value < 70:
        return "BUY"
    elif trend == "DOWN" and rsi_value > 30:
        return "SELL"
    else:
        return "HOLD"