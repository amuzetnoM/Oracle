# Universal Data Loading Guide

## The Argmax Equation Predicts ANYTHING

The fundamental principle of ORXL is the argmax equation:

$$\hat{x} = \arg\max_{x \in \mathcal{C}} S(x \mid c)$$

This equation is **domain-agnostic** and can predict:
- Market movements 📈
- Weather patterns ☁️
- Sensor readings 📡
- Health metrics ❤️
- Text sentiment 📝
- System performance 🖥️
- **ANYTHING with sequential data**

The `UniversalFileProvider` ensures you can feed ANY type of data into ORXL's prediction engine.

---

## Quick Start: Universal Data

### 1. Use Universal Provider

```python
from src.data_ingestion.providers import UniversalFileProvider

# Flexible mode - accepts any columns
provider = UniversalFileProvider(
    data_directory='data/universal_data',
    schema_mode='flexible'
)

# Market mode - enforces OHLCV schema (backward compatible)
provider = UniversalFileProvider(
    data_directory='data/market_data',
    schema_mode='market'
)

# Minimal mode - requires timestamp + at least one numeric column
provider = UniversalFileProvider(
    data_directory='data/sensor_data',
    schema_mode='minimal'
)
```

### 2. Schema Modes Explained

| Mode | Requirements | Use Case |
|------|-------------|----------|
| **flexible** | timestamp + any columns | Any data type, preserves all columns |
| **market** | timestamp + close/price | Market data (OHLCV), backward compatible |
| **minimal** | timestamp + 1 numeric col | Simple time series |

---

## Universal Data Examples

### Example 1: Weather Prediction

**Data**: `weather_NYC.csv`
```csv
timestamp,temperature,humidity,pressure,wind_speed,conditions
2024-01-01T00:00:00Z,32.5,65.0,1013.2,10.5,clear
2024-01-01T01:00:00Z,31.8,68.0,1013.5,12.0,clear
2024-01-01T02:00:00Z,31.0,70.0,1013.8,11.5,cloudy
```

**Usage**:
```python
from src.data_ingestion.providers import UniversalFileProvider
from datetime import datetime

provider = UniversalFileProvider('data/weather')

# Get current weather
current = provider.fetch_current_price('weather_NYC')
print(f"Temperature: {current['temperature']}°F")
print(f"Humidity: {current['humidity']}%")
print(f"Pressure: {current['pressure']} hPa")

# Get historical weather for prediction
historical = provider.fetch_historical_data(
    'weather_NYC',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Predict tomorrow's temperature using argmax
# (integrate with prediction_core as shown later)
```

### Example 2: Sensor Monitoring

**Data**: `sensor_factory_01.json`
```json
[
  {
    "timestamp": "2024-01-01T00:00:00Z",
    "sensor_reading": 98.5,
    "battery_level": 100,
    "signal_strength": 95,
    "temperature": 22.5,
    "vibration": 0.2
  },
  {
    "timestamp": "2024-01-01T00:05:00Z",
    "sensor_reading": 99.2,
    "battery_level": 99,
    "signal_strength": 94,
    "temperature": 22.8,
    "vibration": 0.3
  }
]
```

**Usage**:
```python
provider = UniversalFileProvider('data/sensors')

# Monitor sensor
data = provider.fetch_current_price('sensor_factory_01')
print(f"Reading: {data['sensor_reading']}")
print(f"Battery: {data['battery_level']}%")
print(f"Temperature: {data['temperature']}°C")

# Predict sensor failure (anomaly detection)
historical = provider.fetch_historical_data(
    'sensor_factory_01',
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now()
)
```

### Example 3: Text Sentiment Analysis

**Data**: `social_media_product_X.csv`
```csv
timestamp,sentiment_score,engagement,shares,comments,word_count
2024-01-01T08:00:00Z,0.75,1250,45,23,280
2024-01-01T09:00:00Z,0.82,1580,67,34,310
2024-01-01T10:00:00Z,0.68,980,28,15,245
```

**Usage**:
```python
provider = UniversalFileProvider('data/social_analytics')

# Get current sentiment
current = provider.fetch_current_price('social_media_product_X')
print(f"Sentiment: {current['sentiment_score']}")
print(f"Engagement: {current['engagement']}")

# Predict sentiment trend
historical = provider.fetch_historical_data(
    'social_media_product_X',
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now()
)
```

### Example 4: Health Monitoring

**Data**: `patient_123_vitals.csv`
```csv
timestamp,heart_rate,blood_pressure_sys,blood_pressure_dia,temperature,oxygen_saturation
2024-01-01T08:00:00Z,72,120,80,98.6,98
2024-01-01T08:15:00Z,75,122,82,98.7,97
2024-01-01T08:30:00Z,70,118,78,98.5,98
```

**Usage**:
```python
provider = UniversalFileProvider('data/health')

# Monitor patient vitals
vitals = provider.fetch_current_price('patient_123_vitals')
print(f"Heart Rate: {vitals['heart_rate']} bpm")
print(f"BP: {vitals['blood_pressure_sys']}/{vitals['blood_pressure_dia']}")
print(f"O2: {vitals['oxygen_saturation']}%")

# Predict health anomalies
historical = provider.fetch_historical_data(
    'patient_123_vitals',
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now()
)
```

### Example 5: System Performance

**Data**: `server_metrics.parquet`
```python
# Create parquet file
import pandas as pd

data = {
    'timestamp': pd.date_range('2024-01-01', periods=100, freq='1min'),
    'cpu_usage': [50 + i % 30 for i in range(100)],
    'memory_usage': [60 + i % 20 for i in range(100)],
    'disk_io': [1000 + i * 10 for i in range(100)],
    'network_traffic': [500 + i * 5 for i in range(100)],
    'response_time': [100 + i % 50 for i in range(100)]
}

df = pd.DataFrame(data)
df.to_parquet('data/systems/server_metrics.parquet', index=False)
```

**Usage**:
```python
provider = UniversalFileProvider('data/systems')

# Monitor server
metrics = provider.fetch_current_price('server_metrics')
print(f"CPU: {metrics['cpu_usage']}%")
print(f"Memory: {metrics['memory_usage']}%")
print(f"Response Time: {metrics['response_time']}ms")

# Predict performance issues
historical = provider.fetch_historical_data(
    'server_metrics',
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now()
)
```

---

## Full Prediction Pipeline: Universal Data

### Weather Prediction Example

```python
from src.data_ingestion.providers import UniversalFileProvider
from src.feature_engineering import FeatureCalculator
from src.prediction_core import CandidateSpace, ArgmaxEngine
from src.prediction_core.scoring import StatisticalScorer
import numpy as np
from datetime import datetime, timedelta

# Step 1: Load weather data
provider = UniversalFileProvider('data/weather')
historical = provider.fetch_historical_data(
    'weather_NYC',
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now()
)

# Step 2: Extract features
temperatures = np.array([d['temperature'] for d in historical])
humidity = np.array([d['humidity'] for d in historical])
pressure = np.array([d['pressure'] for d in historical])

# Create context vectors (last 24 hours of data)
contexts = []
outcomes = []

for i in range(24, len(temperatures) - 1):
    # Context: last 24 hours
    context = np.array([
        np.mean(temperatures[i-24:i]),  # avg temp
        np.mean(humidity[i-24:i]),      # avg humidity
        np.mean(pressure[i-24:i]),      # avg pressure
        temperatures[i] - temperatures[i-1],  # temp change
    ])
    
    # Outcome: temperature direction next hour
    outcome = 'warmer' if temperatures[i+1] > temperatures[i] else 'cooler'
    
    contexts.append(context)
    outcomes.append(outcome)

# Step 3: Train prediction model
candidate_space = CandidateSpace(
    candidate_type='custom',
    candidates=['warmer', 'cooler', 'same']
)
scorer = StatisticalScorer(candidate_space)
scorer.train(contexts, outcomes)

# Step 4: Make prediction
latest_context = np.array([
    np.mean(temperatures[-24:]),
    np.mean(humidity[-24:]),
    np.mean(pressure[-24:]),
    temperatures[-1] - temperatures[-2],
])

engine = ArgmaxEngine(candidate_space, scorer)
prediction = engine.predict(latest_context)

print(f"Weather Prediction: {prediction}")
```

### Sensor Anomaly Detection

```python
from src.data_ingestion.providers import UniversalFileProvider
import numpy as np

provider = UniversalFileProvider('data/sensors')
historical = provider.fetch_historical_data(
    'sensor_factory_01',
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Extract readings
readings = np.array([d['sensor_reading'] for d in historical])

# Calculate statistics
mean = np.mean(readings)
std = np.std(readings)

# Predict if current reading is anomalous
current = provider.fetch_current_price('sensor_factory_01')
z_score = abs((current['sensor_reading'] - mean) / std)

if z_score > 3:
    print("⚠️ ANOMALY DETECTED!")
    print(f"Current: {current['sensor_reading']}, Expected: {mean:.2f}±{std:.2f}")
else:
    print("✓ Normal operation")
```

---

## Data Format Requirements

### Universal Format (Flexible Mode)

**Minimum Required**:
```csv
timestamp,value
2024-01-01,100.5
```

**Recommended**:
```csv
timestamp,primary_metric,feature1,feature2,feature3
2024-01-01,100.5,25.3,0.8,normal
```

**All Columns Preserved**: Any additional columns are automatically included.

### Column Name Flexibility

The provider auto-detects common timestamp names:
- `timestamp` ← `date`, `datetime`, `time`, `ts`, `sequence`

All other column names are preserved exactly as provided.

### Supported Data Types

- **Numeric**: Integer, float (for measurements)
- **Datetime**: Timestamps in any standard format
- **String**: Categories, labels, text (preserved but not used in numeric predictions)
- **Boolean**: Flags, binary indicators

---

## Creating Domain-Specific Data Templates

### Template: Weather Data
```csv
timestamp,temperature,humidity,pressure,wind_speed,precipitation,conditions
2024-01-01T00:00:00Z,32.5,65.0,1013.2,10.5,0.0,clear
```

### Template: Sensor Data
```csv
timestamp,reading,battery,signal,temperature,status
2024-01-01T00:00:00Z,98.5,100,95,22.5,normal
```

### Template: Health Vitals
```csv
timestamp,heart_rate,blood_pressure_sys,blood_pressure_dia,temperature,spo2
2024-01-01T08:00:00Z,72,120,80,98.6,98
```

### Template: Text Metrics
```csv
timestamp,sentiment_score,engagement,shares,comments,word_count
2024-01-01T08:00:00Z,0.75,1250,45,23,280
```

### Template: System Metrics
```csv
timestamp,cpu_usage,memory_usage,disk_io,network_traffic,response_time
2024-01-01T00:00:00Z,45.2,62.8,1500,750,105
```

---

## Configuration

### Universal Provider Configuration

Edit `config/providers.yaml`:

```yaml
providers:
  file:
    enabled: true
    data_directory: "data/universal_data"  # Universal data location
    supported_formats:
      - "csv"
      - "json"
      - "parquet"
    schema_mode: "flexible"  # Options: flexible, market, minimal
    scan_subdirectories: true
```

### Multiple Data Domains

Organize by domain:

```
data/
├── weather/
│   ├── NYC.csv
│   └── LA.csv
├── sensors/
│   ├── factory_01.json
│   └── factory_02.json
├── health/
│   ├── patient_123.csv
│   └── patient_456.csv
└── market/
    ├── AAPL.csv
    └── GOOGL.csv
```

Use domain-specific providers:

```python
weather_provider = UniversalFileProvider('data/weather', schema_mode='flexible')
sensor_provider = UniversalFileProvider('data/sensors', schema_mode='minimal')
market_provider = UniversalFileProvider('data/market', schema_mode='market')
```

---

## Advanced: Custom Prediction Domains

### Example: Custom E-commerce Predictions

**Data**: `product_sales.csv`
```csv
timestamp,sales,page_views,cart_adds,conversions,avg_price,inventory
2024-01-01,450,12500,780,450,49.99,1200
2024-01-02,520,13200,850,520,49.99,680
```

**Prediction**: Next day sales volume

```python
provider = UniversalFileProvider('data/ecommerce')
historical = provider.fetch_historical_data(
    'product_sales',
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now()
)

# Build contexts
sales = np.array([d['sales'] for d in historical])
page_views = np.array([d['page_views'] for d in historical])
conversions = np.array([d['conversions'] for d in historical])

contexts = []
outcomes = []

for i in range(7, len(sales) - 1):
    # Context: last 7 days
    context = np.array([
        np.mean(sales[i-7:i]),
        np.mean(page_views[i-7:i]),
        np.mean(conversions[i-7:i]),
        sales[i] - sales[i-1]  # trend
    ])
    
    # Outcome: sales category tomorrow
    if sales[i+1] > sales[i] * 1.1:
        outcome = 'surge'
    elif sales[i+1] < sales[i] * 0.9:
        outcome = 'decline'
    else:
        outcome = 'stable'
    
    contexts.append(context)
    outcomes.append(outcome)

# Train and predict
candidate_space = CandidateSpace(
    candidate_type='custom',
    candidates=['surge', 'stable', 'decline']
)
scorer = StatisticalScorer(candidate_space)
scorer.train(contexts, outcomes)

engine = ArgmaxEngine(candidate_space, scorer)
prediction = engine.predict(contexts[-1])

print(f"Sales Prediction: {prediction}")
```

---

## Best Practices for Universal Data

### 1. **Consistent Timestamps**
Always use consistent timestamp formats within a file:
- ✅ ISO 8601: `2024-01-01T00:00:00Z`
- ✅ Unix: `1704067200`
- ❌ Mixed formats in same file

### 2. **Meaningful Column Names**
Use descriptive names that indicate what you're measuring:
- ✅ `temperature_celsius`, `heart_rate_bpm`
- ❌ `col1`, `data`, `value`

### 3. **Regular Sampling**
Maintain consistent time intervals when possible:
- Hourly: 00:00, 01:00, 02:00...
- Daily: same time each day
- Event-based: OK if timestamps are accurate

### 4. **Document Your Schema**
Create a README for each data domain:
```markdown
# Weather Data Schema

- timestamp: UTC datetime
- temperature: Fahrenheit
- humidity: Percentage (0-100)
- pressure: hPa
- wind_speed: mph
- conditions: categorical (clear/cloudy/rain/snow)
```

### 5. **Test Your Data**
```python
# Verify data loads correctly
provider = UniversalFileProvider('data/your_domain')
schema = provider.get_data_schema('your_file')
print(f"Schema: {schema}")

# Check for missing values
data = provider.fetch_current_price('your_file')
print(f"Latest: {data}")
```

---

## Summary

The `UniversalFileProvider` enables ORXL to predict **anything**:

✅ **Weather** - temperature, precipitation, conditions  
✅ **Sensors** - readings, battery, signal  
✅ **Health** - vitals, metrics, symptoms  
✅ **Text** - sentiment, engagement, metrics  
✅ **Systems** - CPU, memory, performance  
✅ **Finance** - prices, volumes (backward compatible)  
✅ **E-commerce** - sales, traffic, conversions  
✅ **Any sequential data you can imagine**

The argmax equation $\hat{x} = \arg\max_{x \in \mathcal{C}} S(x \mid c)$ is truly universal. This provider ensures you can feed it the correct data and formats to predict anything in the universe.

---

## Next Steps

1. **Choose Your Domain**: Weather, sensors, health, or custom
2. **Prepare Your Data**: Use templates as guides
3. **Create Provider**: `UniversalFileProvider(your_data_dir)`
4. **Build Pipeline**: Load → Features → Predict
5. **Iterate**: Refine context and candidate space

For more information:
- [Data Input Handbook](data_input_handbook.md) - Market data focus
- [Quick Start Guide](file_mode_quickstart.md) - Fast setup
- [ORXL Architecture](../_dev/architecture.md) - System design
- [Mathematical Foundation](../_dev/thesis.md) - Argmax equation
