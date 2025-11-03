# Trading Database Schema

## Schema
### 1. 1-Minute Bar Table (Partitioned by Month)

```
CREATE TABLE bars_1m (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open NUMERIC(18,8) NOT NULL,
    high NUMERIC(18,8) NOT NULL,
    low NUMERIC(18,8) NOT NULL,
    close NUMERIC(18,8) NOT NULL,
    volume NUMERIC(20,4) NOT NULL,
    PRIMARY KEY (ts, symbol)
) PARTITION BY RANGE (ts);
```

Indexing hint: Create a separate partition for each month.

Example:
```
CREATE TABLE bars_1m_2025_01
PARTITION OF bars_1m
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

---

### 2. Orders Table

```
CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT CHECK (side IN ('BUY', 'SELL')) NOT NULL,
    qty NUMERIC(18,4) NOT NULL,
    price NUMERIC(18,8),
    status TEXT NOT NULL  -- e.g., SUBMITTED, FILLED, CANCELLED
);
```

```
CREATE INDEX idx_orders_strategy_ts
ON orders (strategy_id, ts DESC);
```

---

### 3. Trades Table

```
CREATE TABLE trades (
    trade_id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(order_id),
    strategy_id TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT CHECK (side IN ('BUY', 'SELL')) NOT NULL,
    qty NUMERIC(18,4) NOT NULL,
    price NUMERIC(18,8) NOT NULL,
    fee NUMERIC(18,8) DEFAULT 0,
    pnl NUMERIC(18,8), -- optional field for convenience
    UNIQUE (order_id, trade_id)
);
```

```
CREATE INDEX idx_trades_strategy_ts
ON trades (strategy_id, ts DESC);
```

---

### 4. Positions Table (Snapshot Table)

```
CREATE TABLE positions (
    strategy_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    qty NUMERIC(18,4) NOT NULL,
    avg_price NUMERIC(18,8) NOT NULL,
    PRIMARY KEY (strategy_id, symbol, ts)
);
```

---

### 5. Daily PnL Table

```
CREATE TABLE pnl_daily (
    strategy_id TEXT NOT NULL,
    date DATE NOT NULL,
    realized_pnl NUMERIC(18,8) NOT NULL,
    unrealized_pnl NUMERIC(18,8) NOT NULL,
    PRIMARY KEY (strategy_id, date)
);
```

```
CREATE INDEX idx_pnl_daily_strategy_date
ON pnl_daily (strategy_id, date DESC);
```

## SQL Queries
### 1. Rollup + Max Drawdown for strategy_id
```
WITH daily_returns AS (
    SELECT
        date,
        realized_pnl + unrealized_pnl AS total_pnl
    FROM pnl_daily
    WHERE strategy_id = 'STRAT-01'
    ORDER BY date
), equity AS (
    SELECT
        date,
        SUM(total_pnl) OVER (ORDER BY date) AS cumulative_equity
    FROM daily_returns
), drawdown AS (
    SELECT
        date,
        cumulative_equity,
        cumulative_equity - MAX(cumulative_equity) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS drawdown
    FROM equity
)
SELECT
    MIN(drawdown) AS max_drawdown
FROM drawdown;
```
### 2. View: Last Known Position per Symbol
```
CREATE OR REPLACE VIEW last_position_per_symbol AS
SELECT DISTINCT ON (strategy_id, symbol)
    strategy_id,
    symbol,
    ts,
    qty,
    avg_price
FROM positions
ORDER BY strategy_id, symbol, ts DESC;
```

### 3. 30-Day Rolling Sharpe Ratio from pnl_daily
 - Assuming a risk-free rate of 0 and Sharpe = avg(returns) / stddev(returns)

```
WITH rolling_returns AS (
    SELECT
        strategy_id,
        date,
        realized_pnl + unrealized_pnl AS total_pnl,
        AVG(realized_pnl + unrealized_pnl) OVER (
            PARTITION BY strategy_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS avg_30d,
        STDDEV_POP(realized_pnl + unrealized_pnl) OVER (
            PARTITION BY strategy_id ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS std_30d
    FROM pnl_daily
)
SELECT
    strategy_id,
    date,
    CASE WHEN std_30d = 0 THEN NULL
         ELSE avg_30d / std_30d
    END AS sharpe_30d
FROM rolling_returns
ORDER BY date DESC;
```


## Data grows 100X
```
Use TimescaleDB with Chunking + Compression

Migrate bars_1m, trades, and positions into TimescaleDB hypertables.

Set CHUNK_TIME_INTERVAL to 1 day or 1 week for high write performance.

Enable native columnar compression for historical data.

Benefits:

Partitioning is automatic.

Indexed time-series storage.

Querying windows (like rolling Sharpe or drawdown) is faster with time_bucket
```
```
We can also use DuckDB as it is very reliable and popular choice for analytics.
```
