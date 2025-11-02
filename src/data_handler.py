# src/data_handler.py

import pandas as pd
from collections import deque
from typing import Dict, List, Deque

class DataHandler:
    def __init__(self, initial_data_path: str, max_length: int = 200):
        self.prices: Dict[str, Deque[float]] = {}
        self.max_length = max_length
        self._load_initial_data(initial_data_path)

    def _load_initial_data(self, file_path: str):
        """Loads initial OHLCV data to warm up the indicators."""
        try:
            df = pd.read_csv(file_path)
            # Assuming the CSV is for a single symbol, and we use the 'close' price
            # For multiple symbols, the logic would need to be more complex.
            # We'll assume 'XYZ' for now as that's the default in the stream.
            if 'close' in df.columns:
                # Filter out any invalid prices from the initial data
                valid_prices = [p for p in df['close'].tolist() if isinstance(p, (int, float)) and p >= 0]
                self.prices['XYZ'] = deque(valid_prices, maxlen=self.max_length)
        except FileNotFoundError:
            # If the file doesn't exist, we'll start with an empty history.
            pass
        except Exception as e:
            print(f"Error loading initial data: {e}")


    def add_tick(self, symbol: str, price: float):
        """Adds a new price tick for a symbol."""
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("Symbol must be a non-empty string.")
        if not isinstance(price, (int, float)) or price < 0:
            raise ValueError("Price must be a non-negative number.")
            
        if symbol not in self.prices:
            self.prices[symbol] = deque(maxlen=self.max_length)
        self.prices[symbol].append(price)

    def get_prices(self, symbol: str) -> List[float]:
        """Returns the list of prices for a symbol."""
        return list(self.prices.get(symbol, []))

# Initialize a single instance to be used by the FastAPI app
data_handler = DataHandler('ohlcv.csv')