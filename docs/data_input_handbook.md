# Data Input Methods Handbook

## Overview

ORXL (Oracle Argmax Prediction System) supports multiple methods for ingesting market data. This handbook provides comprehensive documentation on all data input types, formats, and best practices.

## Data Input Modes

ORXL operates in two primary data input modes:

### 1. Online API Mode (Default)
Fetches real-time and historical data from online sources via APIs.

### 2. File-Based Mode (New)
Loads data from local files in a designated directory for offline analysis and backtesting.

---

## File-Based Data Loading

### Why File-Based Mode?

- **Offline Analysis**: Work without internet connectivity
- **Backtesting**: Test strategies on historical data
- **Custom Data Sources**: Use proprietary or non-standard data
- **Data Control**: Full control over data quality and preprocessing
- **Cost Efficiency**: Avoid API rate limits and costs
- **Reproducibility**: Ensure consistent data for repeated analysis

### Getting Started

#### 1. Enable File Provider

Edit `config/providers.yaml`:

```yaml
providers:
  file:
    enabled: true
    data_directory: "data/market_data"
```

#### 2. Create Data Directory

```bash
mkdir -p data/market_data
```

#### 3. Add Data Files

Place your data files in the directory:
```
data/market_data/
├── AAPL.csv          # Apple stock data
├── BTCUSD.json       # Bitcoin data
├── gold.parquet      # Gold prices
└── historical/       # Subdirectories supported
    └── SPY.csv       # S&P 500 ETF
```

### Supported File Formats

#### CSV (Comma-Separated Values)

**Advantages**: 
- Human-readable
- Universal support
- Easy to create and edit

**Example**: `AAPL.csv`
```csv
timestamp,open,high,low,close,volume
2024-01-01T00:00:00Z,150.00,152.50,149.50,151.00,1000000
2024-01-02T00:00:00Z,151.00,153.00,150.50,152.50,1200000
2024-01-03T00:00:00Z,152.50,154.00,151.50,153.50,1100000
```

**Usage**:
```python
from src.data_ingestion.providers import FileDataProvider

provider = FileDataProvider('data/market_data')
data = provider.fetch_current_price('AAPL')
```

#### JSON (JavaScript Object Notation)

**Advantages**:
- Structured data
- Supports nested information
- Web-friendly format

**Format 1 - JSON Array**: `BTCUSD.json`
```json
[
  {
    "timestamp": "2024-01-01T00:00:00Z",
    "open": 45000.00,
    "high": 46000.00,
    "low": 44500.00,
    "close": 45500.00,
    "volume": 1000.50
  },
  {
    "timestamp": "2024-01-02T00:00:00Z",
    "open": 45500.00,
    "high": 47000.00,
    "low": 45000.00,
    "close": 46500.00,
    "volume": 1200.75
  }
]
```

**Format 2 - Line-Delimited JSON (JSONL)**: `MSFT.jsonl`
```jsonl
{"timestamp": "2024-01-01T00:00:00Z", "open": 380.00, "high": 385.00, "low": 378.00, "close": 383.00, "volume": 500000}
{"timestamp": "2024-01-02T00:00:00Z", "open": 383.00, "high": 388.00, "low": 381.00, "close": 386.00, "volume": 550000}
```

**Usage**:
```python
provider = FileDataProvider()
data = provider.fetch_historical_data(
    'BTCUSD',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

#### Parquet (Apache Parquet)

**Advantages**:
- Highly compressed
- Fast read/write
- Columnar storage
- Ideal for large datasets

**Requirements**:
```bash
pip install pyarrow
```

**Creation Example**:
```python
import pandas as pd

df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=100),
    'open': [100 + i for i in range(100)],
    'high': [102 + i for i in range(100)],
    'low': [98 + i for i in range(100)],
    'close': [101 + i for i in range(100)],
    'volume': [1000000 for i in range(100)]
})

df.to_parquet('data/market_data/SPY.parquet', index=False)
```

**Usage**:
```python
provider = FileDataProvider()
data = provider.fetch_current_price('SPY')
```

---

## Data Format Specification

### Required Columns

Every data file **MUST** contain:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime/string/unix | Date and time of the data point |
| `close` | float | Closing price (minimum required price field) |

### Optional Columns

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `open` | float | `close` | Opening price |
| `high` | float | `close` | Highest price |
| `low` | float | `close` | Lowest price |
| `volume` | float | 0.0 | Trading volume |

### Column Name Flexibility

ORXL automatically recognizes common alternative column names:

- **timestamp**: `date`, `datetime`, `time`, `ts`
- **close**: `price`, `last`

Column names are case-insensitive: `Timestamp`, `TIMESTAMP`, `timestamp` all work.

### Timestamp Formats

ORXL supports multiple timestamp formats:

#### ISO 8601 String (Recommended)
```
2024-01-01T00:00:00Z
2024-01-01T09:30:00-05:00
2024-01-01 09:30:00
```

#### Unix Timestamp (Seconds)
```
1704067200
1704153600.5
```

#### Pandas-Compatible Formats
Any format parseable by `pd.to_datetime()`:
```
01/01/2024
2024-01-01
Jan 1, 2024
```

---

## Complete Data Templates

### Template 1: Minimal CSV (Close Price Only)
```csv
timestamp,close
2024-01-01,100.50
2024-01-02,101.25
2024-01-03,100.75
```

### Template 2: Standard OHLCV CSV
```csv
timestamp,open,high,low,close,volume
2024-01-01T09:30:00Z,100.00,101.50,99.50,100.50,1000000
2024-01-02T09:30:00Z,100.50,102.00,100.00,101.25,1200000
2024-01-03T09:30:00Z,101.25,101.50,99.75,100.75,1100000
```

### Template 3: Extended Data with Custom Fields
```csv
timestamp,open,high,low,close,volume,symbol,exchange
2024-01-01T09:30:00Z,100.00,101.50,99.50,100.50,1000000,AAPL,NASDAQ
2024-01-02T09:30:00Z,100.50,102.00,100.00,101.25,1200000,AAPL,NASDAQ
```
*Note: Extra columns are preserved but not used by core system*

### Template 4: Intraday High-Frequency Data
```csv
timestamp,close,volume
2024-01-01T09:30:00Z,100.50,1000
2024-01-01T09:31:00Z,100.55,1200
2024-01-01T09:32:00Z,100.52,1100
2024-01-01T09:33:00Z,100.60,1500
```

---

## Data Validation

ORXL performs automatic validation on all loaded data:

### Price Validation
- Prices must be positive numbers
- Default range: 0 to 1 billion
- Configurable in `config/providers.yaml`

### OHLC Consistency
- `high >= low`
- `high >= open` and `high >= close`
- `low <= open` and `low <= close`

### Timestamp Validation
- Must be valid datetime
- Default range: 2000-01-01 to today + 1 day
- Must be properly ordered (ascending)

### Outlier Detection
- Optional IQR or Z-score methods
- Configurable threshold
- Warnings logged for outliers

Configuration in `config/providers.yaml`:
```yaml
validation:
  price:
    min: 0
    max: 1000000000
  volume:
    min: 0
  timestamp:
    min_year: 2000
    max_future_days: 1
    
normalization:
  outlier_detection:
    enabled: true
    method: "iqr"  # or "zscore"
    threshold: 3.0
```

---

## API Usage Examples

### Example 1: Basic Usage
```python
from src.data_ingestion.providers import FileDataProvider
from datetime import datetime, timedelta

# Initialize provider
provider = FileDataProvider('data/market_data')

# Get current (latest) price
current = provider.fetch_current_price('AAPL')
print(f"AAPL: ${current['close']}")

# Get historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

historical = provider.fetch_historical_data(
    'AAPL',
    start_date=start_date,
    end_date=end_date
)

print(f"Loaded {len(historical)} data points")
```

### Example 2: List Available Symbols
```python
provider = FileDataProvider()

# List all symbols in directory
symbols = provider.list_available_symbols()
print(f"Available symbols: {symbols}")

# Iterate through all symbols
for symbol in symbols:
    data = provider.fetch_current_price(symbol)
    if data:
        print(f"{symbol}: ${data['close']}")
```

### Example 3: Integration with Feature Engineering
```python
from src.data_ingestion.providers import FileDataProvider
from src.feature_engineering import FeatureCalculator
from datetime import datetime, timedelta

# Load data
provider = FileDataProvider()
historical = provider.fetch_historical_data(
    'AAPL',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Convert to arrays for feature calculation
data = {
    'open': [d['open'] for d in historical],
    'high': [d['high'] for d in historical],
    'low': [d['low'] for d in historical],
    'close': [d['close'] for d in historical],
    'volume': [d['volume'] for d in historical]
}

# Calculate features
calculator = FeatureCalculator()
features = calculator.calculate_all(data)

print(f"Calculated features: {list(features.keys())}")
```

### Example 4: Full Prediction Pipeline
```python
from src.data_ingestion.providers import FileDataProvider
from src.feature_engineering import FeatureCalculator
from src.prediction_core import CandidateSpace, ArgmaxEngine
from src.prediction_core.scoring import StatisticalScorer
import numpy as np
from datetime import datetime, timedelta

# Step 1: Load data
provider = FileDataProvider()
historical = provider.fetch_historical_data(
    'AAPL',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)

# Step 2: Prepare data
prices = np.array([d['close'] for d in historical])
returns = np.diff(prices) / prices[:-1]

# Step 3: Create prediction system
candidate_space = CandidateSpace(candidate_type='direction')
scorer = StatisticalScorer(candidate_space)

# Step 4: Train
contexts = []
outcomes = []
for i in range(20, len(returns) - 1):
    context = returns[i-5:i]
    outcome = 'up' if returns[i] > 0 else 'down'
    contexts.append(context)
    outcomes.append(outcome)

scorer.train(contexts, outcomes)

# Step 5: Predict
latest_context = returns[-5:]
engine = ArgmaxEngine(candidate_space, scorer)
prediction = engine.predict(latest_context)

print(f"Prediction: {prediction}")
```

---

## Best Practices

### 1. File Organization
- Use clear, consistent naming: `SYMBOL.format`
- One symbol per file
- Organize by asset class: `stocks/`, `crypto/`, `commodities/`
- Keep related data together

### 2. Data Quality
- Ensure data is sorted by timestamp (ascending)
- Remove duplicate timestamps
- Fill or interpolate missing values
- Validate data before adding to system
- Document data sources and transformations

### 3. Performance Optimization
- Use Parquet for large datasets (>1GB)
- Use CSV for small datasets and human readability
- Use JSON for structured/nested data
- Compress files when storing long-term
- Keep actively used data uncompressed

### 4. File Naming Conventions
```
# Good
AAPL.csv          # Stock ticker
BTCUSD.json       # Crypto pair
GOLD.parquet      # Commodity

# Avoid
apple_stock.csv   # Non-standard name
aapl_data.csv     # Underscore ambiguity
AAPL_2024.csv     # Date in filename (use file content)
```

### 5. Data Updates
```python
# Refresh file cache after adding new files
provider = FileDataProvider()
provider.refresh_cache()

# Or configure auto-refresh
# In config/providers.yaml:
# file:
#   refresh_on_request: true
```

---

## Troubleshooting

### Issue: "No data file found for symbol"
**Cause**: File doesn't exist or naming mismatch  
**Solution**: 
- Check file exists in `data_directory`
- Ensure filename matches symbol (case-insensitive)
- Run `provider.list_available_symbols()` to see available symbols

### Issue: "Missing required column: timestamp"
**Cause**: Data file missing timestamp column  
**Solution**:
- Add `timestamp` column to file
- Or rename existing date column to `timestamp`
- Supported alternatives: `date`, `datetime`, `time`, `ts`

### Issue: "Could not parse timestamp column"
**Cause**: Invalid timestamp format  
**Solution**:
- Use ISO 8601 format: `2024-01-01T00:00:00Z`
- Or Unix timestamp (seconds): `1704067200`
- Ensure consistent format throughout file

### Issue: "Validation failed - Price out of range"
**Cause**: Price exceeds configured limits  
**Solution**:
- Check price values are correct
- Adjust validation limits in `config/providers.yaml`:
```yaml
validation:
  price:
    min: 0
    max: 10000000000  # Increase limit
```

### Issue: "Error loading Parquet file"
**Cause**: Missing pyarrow dependency  
**Solution**:
```bash
pip install pyarrow
```

---

## Summary

ORXL's file-based data loading provides:

✅ **Flexibility**: Multiple file formats (CSV, JSON, Parquet)  
✅ **Simplicity**: Automatic column detection and normalization  
✅ **Robustness**: Comprehensive validation and error handling  
✅ **Performance**: Efficient caching and optimized formats  
✅ **Reliability**: Works offline, no API dependencies  

The file provider integrates seamlessly with the ORXL prediction pipeline, maintaining the mathematical rigor and precision of the argmax equation while providing complete control over your data sources.

For more information, see:
- [ORXL Architecture](_dev/architecture.md)
- [Mathematical Foundations](_dev/thesis.md)
- [README](../README.md)
