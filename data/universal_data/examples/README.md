# Universal Data Templates

This directory contains example data templates for various prediction domains. The argmax equation can predict **anything** - these templates show you how to format data for different use cases.

## Available Templates

### 1. Weather Data (`weather/weather_template.csv`)
**Domain**: Meteorology, climate prediction  
**Use Cases**: Temperature forecasting, precipitation prediction, weather pattern analysis  
**Columns**:
- `timestamp`: UTC datetime
- `temperature`: Temperature in Fahrenheit
- `humidity`: Relative humidity (%)
- `pressure`: Atmospheric pressure (hPa)
- `wind_speed`: Wind speed (mph)
- `precipitation`: Rainfall (inches)
- `conditions`: Weather condition (categorical)

### 2. Sensor Data (`sensors/sensor_template.json`)
**Domain**: IoT, industrial monitoring, smart devices  
**Use Cases**: Predictive maintenance, anomaly detection, equipment monitoring  
**Columns**:
- `timestamp`: UTC datetime
- `sensor_reading`: Primary sensor measurement
- `battery_level`: Battery charge (%)
- `signal_strength`: Signal quality (%)
- `temperature`: Operating temperature (°C)
- `vibration`: Vibration level
- `status`: Operational status (categorical)

### 3. Health Vitals (`health/health_vitals_template.csv`)
**Domain**: Healthcare, patient monitoring, wellness tracking  
**Use Cases**: Health anomaly detection, trend analysis, predictive alerts  
**Columns**:
- `timestamp`: Local datetime
- `heart_rate`: Beats per minute (bpm)
- `blood_pressure_sys`: Systolic pressure (mmHg)
- `blood_pressure_dia`: Diastolic pressure (mmHg)
- `temperature`: Body temperature (°F)
- `oxygen_saturation`: SpO2 (%)
- `respiratory_rate`: Breaths per minute

### 4. Text Metrics (`text/text_metrics_template.csv`)
**Domain**: Social media, content analysis, sentiment tracking  
**Use Cases**: Sentiment prediction, engagement forecasting, trend detection  
**Columns**:
- `timestamp`: UTC datetime
- `sentiment_score`: Sentiment (0-1, negative to positive)
- `engagement`: Total engagement count
- `shares`: Number of shares
- `comments`: Number of comments
- `word_count`: Text length
- `topic`: Content topic (categorical)

### 5. System Metrics (`systems/system_metrics_template.csv`)
**Domain**: IT infrastructure, DevOps, performance monitoring  
**Use Cases**: Performance prediction, capacity planning, anomaly detection  
**Columns**:
- `timestamp`: UTC datetime
- `cpu_usage`: CPU utilization (%)
- `memory_usage`: Memory utilization (%)
- `disk_io`: Disk I/O (MB/s)
- `network_traffic`: Network traffic (MB/s)
- `response_time`: Response time (ms)
- `active_connections`: Active connections count

## How to Use These Templates

### 1. Copy Template
```bash
cp data/universal_data/examples/weather/weather_template.csv data/universal_data/my_weather.csv
```

### 2. Replace with Your Data
Edit the file with your actual measurements, keeping the column structure.

### 3. Load and Predict
```python
from src.data_ingestion.providers import UniversalFileProvider

provider = UniversalFileProvider('data/universal_data')
data = provider.fetch_current_price('my_weather')
print(f"Current temperature: {data['temperature']}°F")
```

## Creating Custom Templates

### Minimum Requirements
Every data file MUST have:
1. **timestamp**: Time identifier (any standard datetime format)
2. **At least one numeric column**: Your measurement/value

### Example: Custom E-commerce Data
```csv
timestamp,sales,page_views,cart_adds,conversions,revenue
2024-01-01,450,12500,780,450,22495.50
2024-01-02,520,13200,850,520,25994.80
```

### Example: Custom Environmental Data
```csv
timestamp,air_quality_index,pm25,pm10,co2,noise_level
2024-01-01T00:00:00Z,45,12.5,20.8,410,55.2
2024-01-01T01:00:00Z,48,13.2,21.5,415,52.8
```

## Schema Modes

Choose the right mode for your data:

### Flexible Mode (Recommended for Universal Data)
```python
provider = UniversalFileProvider('data/universal_data', schema_mode='flexible')
```
- Accepts any columns
- Preserves all data
- Best for custom domains

### Market Mode (For Financial Data)
```python
provider = UniversalFileProvider('data/market_data', schema_mode='market')
```
- Enforces OHLCV schema
- Backward compatible
- Use for price data

### Minimal Mode (For Simple Time Series)
```python
provider = UniversalFileProvider('data/simple_data', schema_mode='minimal')
```
- Only requires timestamp + one numeric column
- Simplest setup
- Good for basic predictions

## Data Quality Tips

1. **Consistent Timestamps**: Use same format throughout file
2. **No Missing Values**: Fill or interpolate gaps
3. **Proper Units**: Document units in column names or README
4. **Regular Sampling**: Maintain consistent intervals when possible
5. **Validate**: Test load before using in production

## Next Steps

1. Choose a template matching your domain
2. Customize with your data
3. Load with `UniversalFileProvider`
4. Build prediction pipeline with argmax engine
5. See [Universal Data Guide](../../../docs/universal_data_guide.md) for examples

## Support

- **Flexible schema**: Any columns work
- **Multiple formats**: CSV, JSON, Parquet
- **Case-insensitive**: Column names are normalized
- **Auto-detection**: Common timestamp names recognized

The argmax equation predicts **anything**. These templates help you format your data correctly to unleash its full power.
