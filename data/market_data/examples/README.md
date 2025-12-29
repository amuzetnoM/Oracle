# Data Templates

This directory contains example data file templates for ORXL file-based data loading.

## Templates Included

### 1. AAPL_template.csv
Standard OHLCV (Open, High, Low, Close, Volume) format.
- **Use for**: Stock, ETF, or any standard market data
- **Format**: CSV with all OHLCV columns
- **Timestamp**: ISO 8601 format

### 2. BTCUSD_template.json
JSON array format for cryptocurrency or other assets.
- **Use for**: Cryptocurrency, forex, or structured data
- **Format**: JSON array of objects
- **Timestamp**: ISO 8601 format

### 3. MINIMAL_template.csv
Minimal format with only required columns (timestamp and close).
- **Use for**: Simple price series or when OHLCV data is unavailable
- **Format**: CSV with minimal columns
- **Timestamp**: Simple date format (automatically parsed)

## How to Use

1. Copy a template file
2. Rename to your symbol (e.g., `MSFT.csv`, `ETHUSD.json`)
3. Replace the data with your actual market data
4. Place in the `data/market_data` directory
5. The file provider will automatically detect and load it

## File Naming Convention

Files should be named using the symbol/ticker:
- `AAPL.csv` - Apple stock
- `BTCUSD.json` - Bitcoin/USD pair
- `GOLD.parquet` - Gold prices
- `SPY.csv` - S&P 500 ETF

**Important**: 
- Filename (without extension) becomes the symbol
- Case-insensitive matching
- One symbol per file

## Data Requirements

### Required Columns
- `timestamp` - Date/time of the data point
- `close` - Closing price

### Optional Columns
- `open` - Opening price (defaults to close if missing)
- `high` - Highest price (defaults to close if missing)
- `low` - Lowest price (defaults to close if missing)
- `volume` - Trading volume (defaults to 0 if missing)

### Timestamp Formats Supported
- ISO 8601: `2024-01-01T09:30:00Z`
- Unix timestamp: `1704067200`
- Simple date: `2024-01-01`
- US format: `01/01/2024`
- Any format parseable by pandas

## Validation

All data is automatically validated:
- Prices must be positive
- OHLC consistency: high >= low, high >= open/close, low <= open/close
- Timestamps must be valid and in chronological order
- Outliers are detected and logged

## For More Information

See the complete documentation:
- [Data Input Handbook](../../../docs/data_input_handbook.md)
- [ORXL README](../../../README.md)
