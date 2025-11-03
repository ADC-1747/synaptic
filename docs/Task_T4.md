# 📄 T4: Learning Sprint — Options & Microstructure  
### 1-Page Synthesis

---

## a) One Microstructure Failure Mode + Mitigation in Runner

### ⚠️ Failure Mode: Naïve Execution at Bar Close
Naïve backtests assume instant execution at the **last traded price (LTP)** or **bar close**. This disregards real-world order book behavior—like **quote staleness** or **latency arbitrage**—leading to:

- Unrealistic fills at prices that are no longer actionable
- Inflated PnL due to optimistic assumptions
- Ignored liquidity constraints (especially in options trading)

---

### 💥 How It Breaks the Backtest

If a backtest executes a market order at bar close without checking:

- **Best bid/ask availability**, and  
- **Depth of liquidity** relative to the order size  

…it effectively **teleports into execution**, ignoring critical live market constraints.

This flaw is even more severe in:

- **Sparse instruments** like options  
- **Volatile periods** (e.g., around expiry)  
- **Wide spreads** scenarios  

---

### 🛠️ Mitigation Plugged into the Runner

✅ **Fix:** Use **QuoteTicks** with staleness checks and a **slippage hook**

#### Example: Quote Helper in `run_backtest()`

```python
# Quote helper inside run_backtest()
def get_best_quote(ts_event):
    quotes = engine.cache.quote_ticks(instrument_id=instrument.id)
    latest = next((q for q in reversed(quotes) if q.ts_event <= ts_event), None)
    return latest if latest and ts_event - latest.ts_event < 5_000_000_000 else None  # 5 sec staleness
```

### 🔧 Modification to `order_factory.market()`

#### ✅ Validate Liquidity Size
Before executing a market order, check if there's sufficient size in the best bid/ask:
- Use `quote.bid_size` for sell orders
- Use `quote.ask_size` for buy orders  
If the available size is smaller than the order quantity → **reject or partially fill**.

#### ❌ Reject or Reprice If Quote Is Stale
- If `get_best_quote()` returns `None` (stale or missing quote):
  - Reject the order, **or**
  - Reprice with a model-based adjustment (e.g., fallback to last valid quote + penalty)

#### 📉 Apply Slippage Model When Quotes Are Thin/Volatile
- Estimate additional slippage based on:
  - Order size vs. available depth
  - Time since last valid quote
  - Volatility of the instrument (e.g., options near expiry)
- Adjust execution price accordingly to prevent **overstated PnL**



### b) Simple Slippage Model + Where It Plugs In

#### 📊 Model Overview
A basic **quote-based slippage model** adjusts the execution price based on order size relative to the available best bid/ask depth.

```python
slippage = min( max(1, floor(order_qty / lot_size)), max_slippage_ticks )
slipped_price = best_price + (slippage * tick_size)
```

### Where It Goes in Code:
Add this just before submitting the order inside your Strategy:
```
def apply_slippage(self, side, raw_price, qty):
    tick_size = self.instrument.price_increment
    est_slip_ticks = min(5, max(1, qty // 1000))  # dumb proportional model
    return raw_price + (est_slip_ticks * tick_size) * (1 if side == OrderSide.BUY else -1)

# Replace raw_price in market order creation:
slipped_price = self.apply_slippage(OrderSide.BUY, bar.close, 1000)
```
Then reflect this in the execution log via ExecEngineConfig.exec_algorithm (current code already hooks in TWAP, so slippage is applied via config too).


### c) Two Sanity Checks Before Live Trading an Options Spread

#### 🗓️ Expiry & Exercise Sanity

- **Check Expiry Alignment**: Ensure both legs of the spread have compatible expiry dates.  
  - Avoid mismatches unless you're intentionally trading calendar spreads.
- **Roll Logic**: Confirm strategy logic handles rolling before the contract's last trading day cut-off.  
  - Typically **T-1 or T-2**, depending on the exchange's rules.
- **Exercise Risk**: Verify you're not at risk of early exercise if one leg goes deep in-the-money.

---

#### ⚠️ Max Loss Envelope Under Stress

- **Stress Test Inputs**:
  - Shock **both legs** by ±2 × ATR (Average True Range), or
  - Apply a **±15% IV crush** (Implied Volatility shock).
  - Re-price both legs and compute the **worst-case Mark-to-Market loss**.
- **Critical Realism Features**:
  - Simulate using **post-bid marks**, not mid prices.
  - Include failure scenarios such as:
    - One leg failing to fill
    - Leg being cut by exchange rules (e.g., due to expiry or market halt)
    - Massive intraday spread widening → **margin calls**
- Many blow-ups occur from optimistic assumptions about intraday convergence — this sanity check keeps you honest.

