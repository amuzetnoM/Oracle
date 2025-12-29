# File-Based Data Mode - Quick Start Guide

## Overview

ORXL now supports loading market data from local files, enabling offline analysis, backtesting, and custom data integration without relying on external APIs.

## 5-Minute Setup

### Step 1: Enable File Provider

Edit `config/providers.yaml` and ensure the file provider is enabled:

```yaml
providers:
  file:
    enabled: true
    data_directory: "data/market_data"
```

### Step 2: Create Data Directory

```bash
mkdir -p data/market_data
```

### Step 3: Add Your Data

Copy one of the templates from `data/market_data/examples/` or create your own:

**Example: AAPL.csv**
```csv
timestamp,open,high,low,close,volume
2024-01-01T09:30:00Z,150.00,152.50,149.50,151.00,1000000
2024-01-02T09:30:00Z,151.00,153.00,150.50,152.50,1200000
2024-01-03T09:30:00Z,152.50,154.00,151.50,153.50,1100000
```

### Step 4: Use the Provider

```python
from src.data_ingestion.providers import FileDataProvider
from datetime import datetime, timedelta

# Initialize provider
provider = FileDataProvider('data/market_data')

# Get current (latest) price
current = provider.fetch_current_price('AAPL')
print(f"AAPL: ${current['close']}")

# Get historical data
historical = provider.fetch_historical_data(
    'AAPL',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 3)
)

print(f"Loaded {len(historical)} data points")
```

## Common Use Cases

### Use Case 1: Backtesting with Historical Data

```python
from src.data_ingestion.providers import FileDataProvider
import numpy as np

# Load historical data
provider = FileDataProvider()
historical = provider.fetch_historical_data(
    'AAPL',
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# Run your strategy
prices = [d['close'] for d in historical]
returns = np.diff(prices) / prices[:-1]
sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
```

### Use Case 2: Custom Data Integration

If you have proprietary data or data from non-standard sources:

```python
import pandas as pd

# Your custom data (from any source)
custom_data = {
    'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03'],
    'close': [100.5, 101.2, 102.8]
}
df = pd.DataFrame(custom_data)

# Save to file
df.to_csv('data/market_data/CUSTOM.csv', index=False)

# Load with ORXL
provider = FileDataProvider()
data = provider.fetch_current_price('CUSTOM')
print(f"Custom data: ${data['close']}")
```

### Use Case 3: Offline Development

Work without internet connectivity:

```python
# Download data once (with internet)
from src.data_ingestion.providers import YFinanceProvider
import pandas as pd

api_provider = YFinanceProvider()
historical = api_provider.fetch_historical_data(
    'SPY',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Save to file
df = pd.DataFrame(historical)
df.to_csv('data/market_data/SPY.csv', index=False)

# Now work offline
file_provider = FileDataProvider()
data = file_provider.fetch_current_price('SPY')
# Works without internet!
```

### Use Case 4: Multi-Symbol Analysis

```python
provider = FileDataProvider()

# List all available symbols
symbols = provider.list_available_symbols()
print(f"Available: {symbols}")

# Analyze all symbols
for symbol in symbols:
    data = provider.fetch_current_price(symbol)
    if data:
        print(f"{symbol}: ${data['close']:.2f} (Volume: {data['volume']:,.0f})")
```

## Supported File Formats

### CSV (Best for Small to Medium Datasets)
- Human-readable
- Easy to edit
- Universal support

### JSON (Best for Structured Data)
- Supports nested data
- Web-friendly
- Two formats: array or line-delimited

### Parquet (Best for Large Datasets)
- Highly compressed
- Fast read/write
- Requires: `pip install pyarrow`

## Data Format Requirements

### Minimum Required
```csv
timestamp,close
2024-01-01,100.50
```

### Full OHLCV (Recommended)
```csv
timestamp,open,high,low,close,volume
2024-01-01T09:30:00Z,100.00,101.50,99.50,100.50,1000000
```

### Column Name Alternatives
ORXL automatically recognizes:
- `timestamp` → `date`, `datetime`, `time`, `ts`
- `close` → `price`, `last`

Column names are case-insensitive.

## Tips & Best Practices

### 1. File Naming
✅ **Good**: `AAPL.csv`, `BTCUSD.json`, `GOLD.parquet`  
❌ **Bad**: `apple_stock.csv`, `aapl_2024.csv`

Filename (without extension) becomes the symbol name.

### 2. Data Organization
```
data/market_data/
├── stocks/
│   ├── AAPL.csv
│   ├── MSFT.csv
│   └── GOOGL.csv
├── crypto/
│   ├── BTCUSD.json
│   └── ETHUSD.json
└── commodities/
    ├── GOLD.csv
    └── SILVER.csv
```

Subdirectories are automatically scanned.

### 3. Timestamp Formats
ORXL accepts multiple formats:
- ISO 8601: `2024-01-01T09:30:00Z` (recommended)
- Unix: `1704067200`
- Simple: `2024-01-01`
- US format: `01/01/2024`

### 4. Performance
- **Small datasets (<10MB)**: Use CSV
- **Medium datasets (10-100MB)**: Use CSV or JSON
- **Large datasets (>100MB)**: Use Parquet

### 5. Updating Data
```python
# Refresh cache after adding new files
provider = FileDataProvider()
provider.refresh_cache()

# Or enable auto-refresh in config
# providers.yaml:
# file:
#   refresh_on_request: true
```

## Troubleshooting

### "No data file found for symbol"
- Check file exists in `data_directory`
- Verify filename matches symbol (case-insensitive)
- Run `provider.list_available_symbols()`

### "Missing required column: timestamp"
- Add `timestamp` column
- Or rename date column to `timestamp`

### "Could not parse timestamp"
- Use ISO 8601 format: `2024-01-01T00:00:00Z`
- Or Unix timestamp: `1704067200`

### Parquet import error
```bash
pip install pyarrow
```

## Migration from API to File Mode

### Option 1: Full Migration
```yaml
# config/providers.yaml
providers:
  yfinance:
    enabled: false  # Disable API
  
  file:
    enabled: true   # Enable file provider
```

### Option 2: Hybrid Mode (Recommended)
Keep both enabled and choose per use case:
```python
# Backtesting - use files
file_provider = FileDataProvider()
historical = file_provider.fetch_historical_data(...)

# Live trading - use API
api_provider = YFinanceProvider()
current = api_provider.fetch_current_price(...)
```

## Advanced Features

### Custom Preprocessing
```python
# preprocess.py
import pandas as pd

def clean_data(input_file, output_file):
    df = pd.read_csv(input_file)
    df = df.dropna()
    df = df.sort_values('timestamp')
    df.to_csv(output_file, index=False)

clean_data('raw/AAPL_raw.csv', 'data/market_data/AAPL.csv')
```

### Automated Updates
```python
# update.py
from src.data_ingestion.providers import YFinanceProvider
import pandas as pd
from pathlib import Path

def update_symbol(symbol):
    # Fetch latest data from API
    api = YFinanceProvider()
    data = api.fetch_historical_data(...)
    
    # Append to file
    file_path = Path('data/market_data') / f'{symbol}.csv'
    existing = pd.read_csv(file_path)
    new_data = pd.DataFrame(data)
    combined = pd.concat([existing, new_data]).drop_duplicates()
    combined.to_csv(file_path, index=False)

# Run daily
for symbol in ['AAPL', 'MSFT', 'GOOGL']:
    update_symbol(symbol)
```

## Complete Example: Full Pipeline

```python
from src.data_ingestion.providers import FileDataProvider
from src.feature_engineering import FeatureCalculator
from src.prediction_core import CandidateSpace, ArgmaxEngine
from src.prediction_core.scoring import StatisticalScorer
import numpy as np
from datetime import datetime

# 1. Load data from file
provider = FileDataProvider()
historical = provider.fetch_historical_data(
    'AAPL',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# 2. Prepare data
prices = np.array([d['close'] for d in historical])
returns = np.diff(prices) / prices[:-1]

# 3. Create and train model
candidate_space = CandidateSpace(candidate_type='direction')
scorer = StatisticalScorer(candidate_space)

contexts = [returns[i-5:i] for i in range(20, len(returns)-1)]
outcomes = ['up' if returns[i] > 0 else 'down' for i in range(20, len(returns)-1)]
scorer.train(contexts, outcomes)

# 4. Make prediction
latest_context = returns[-5:]
engine = ArgmaxEngine(candidate_space, scorer)
prediction = engine.predict(latest_context)

print(f"Prediction for tomorrow: {prediction}")
```

## What's Next?

- Read the [Full Data Input Handbook](data_input_handbook.md)
- Explore [Example Templates](../data/market_data/examples/)
- Learn about [ORXL Architecture](../_dev/architecture.md)
- Understand the [Mathematical Foundation](../_dev/thesis.md)

## Need Help?

- Check [Troubleshooting](#troubleshooting) section above
- Review [Data Input Handbook](data_input_handbook.md) for detailed info
- See [Example Templates](../data/market_data/examples/README.md)
- Open an issue on [GitHub](https://github.com/amuzetnoM/orxl/issues)
