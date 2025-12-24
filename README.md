# Syndicate Argmax Prediction System

**A production-grade, modular prediction system based on the universal argmax equation, built with legacy computing principles for maximum backward compatibility and robustness.**

## 🎯 Overview

Syndicate implements the argmax prediction principle:

$$\hat{x} = \arg\max_{x \in \mathcal{C}} S(x \mid c)$$

This system provides:
- ✅ **Modular Architecture**: 8 independent yet integrated modules
- ✅ **Legacy-First**: No modern ML frameworks - pure numpy/scipy
- ✅ **Production-Ready**: Comprehensive testing, monitoring, and deployment
- ✅ **Beautiful UI**: Real-time web dashboard
- ✅ **Multiple Data Sources**: FRED, yfinance, Binance, CoinGecko, and more

## 📁 Project Structure

```
Syndicate/
├── _dev/                    # Theoretical documentation and research
├── src/                     # Source code (8 modular components)
│   ├── data_ingestion/     # Multi-source data providers
│   ├── feature_engineering/ # Technical indicators (pure numpy)
│   ├── prediction_core/     # Argmax engine and scoring
│   ├── risk_management/     # VaR, CVaR, Kelly criterion
│   ├── execution/           # Order management and execution
│   ├── monitoring/          # Performance tracking and drift detection
│   ├── orchestrator/        # Event-driven coordination
│   └── web_ui/              # Flask + vanilla JS interface
├── config/                  # Configuration files
├── tests/                   # Comprehensive test suite
├── docs/                    # User documentation
├── scripts/                 # Utility scripts
└── data/                    # Data storage (gitignored)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) PostgreSQL for production

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/amuzetnoM/Syndicate.git
   cd Syndicate
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Initialize database**:
   ```bash
   python scripts/setup.sh
   ```

6. **Run the system**:
   ```bash
   python scripts/run_system.sh
   ```

7. **Access the UI**:
   Open your browser to `http://localhost:5000`

## 📚 Documentation

- **[Implementation Plan](_dev/IMPLEMENTATION_PLAN.md)**: Complete system architecture and build plan
- **[Theoretical Foundation](_dev/thesis.md)**: Mathematical basis of the argmax equation
- **[User Guide](docs/user_guide.md)**: Comprehensive usage documentation
- **[API Reference](docs/api_reference.md)**: API documentation
- **[Deployment Guide](docs/deployment.md)**: Production deployment instructions

## 🔧 Configuration

Configuration is managed through:
1. **YAML files** (`config/*.yaml`): System defaults and module settings
2. **Environment variables** (`.env`): Secrets and environment-specific config
3. **Runtime parameters**: API and command-line overrides

See [Configuration Guide](docs/configuration.md) for details.

## 🧪 Testing

Run the complete test suite:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

Run specific test categories:
```bash
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/system/        # End-to-end tests
```

## 📊 Module Overview

### 1. Data Ingestion
Fetches and normalizes data from multiple sources:
- FRED (Federal Reserve Economic Data)
- Yahoo Finance (yfinance)
- Binance (cryptocurrency)
- CoinGecko
- Alpha Vantage

**Standalone use**: Import as data provider library
**Integrated use**: Feeds feature engineering module

### 2. Feature Engineering
Computes technical indicators using pure numpy:
- Moving averages (SMA, EMA, WMA)
- Momentum indicators (RSI, MACD, Stochastic)
- Volatility measures (ATR, Bollinger Bands)
- Volume analysis

**Standalone use**: Technical analysis library
**Integrated use**: Provides context vectors for prediction

### 3. Prediction Core
Implements the argmax equation with multiple scoring functions:
- Statistical (frequency-based)
- Bayesian probability estimation
- Ensemble methods

**Standalone use**: General prediction engine
**Integrated use**: Central prediction system

### 4. Risk Management
Portfolio theory and risk-adjusted position sizing:
- VaR/CVaR calculation
- Kelly criterion
- Maximum drawdown analysis
- Markowitz optimization

**Standalone use**: Risk analysis toolkit
**Integrated use**: Converts predictions to positions

### 5. Execution
Order management and execution:
- Paper trading
- Transaction cost modeling
- Execution strategies (TWAP, VWAP)

**Standalone use**: Trading execution system
**Integrated use**: Executes risk-adjusted signals

### 6. Monitoring & Feedback
Performance tracking and adaptation:
- Real-time metrics
- Drift detection
- Anomaly detection
- Feedback loop for continuous learning

**Standalone use**: System monitoring toolkit
**Integrated use**: Closes the prediction-outcome loop

### 7. Orchestrator
Coordinates all modules:
- Event-driven architecture
- Task scheduling
- Health monitoring
- Circuit breaker pattern

**Standalone use**: General orchestration framework
**Integrated use**: System coordinator

### 8. Web UI
Beautiful real-time dashboard:
- Live predictions and confidence
- Performance metrics
- Risk visualization
- System health monitoring

**Standalone use**: Monitoring interface for any system
**Integrated use**: User interface for Syndicate

## 🔒 Security

- API keys stored in `.env` (never committed)
- External configuration management
- Input validation and sanitization
- Rate limiting and circuit breakers

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

[MIT License](LICENSE)

## 👥 Authors

- **Ali A. Shakil** - Initial theoretical work
- **Syndicate Team** - System implementation

## 🙏 Acknowledgments

- Theoretical foundation based on Bayesian decision theory
- Inspired by PAC learning theory and information theory
- Portfolio theory from Markowitz, Sharpe, and Kelly

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/amuzetnoM/Syndicate/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amuzetnoM/Syndicate/discussions)

---

**Built with ❤️ using legacy computing principles for maximum robustness and backward compatibility.**

*No modern ML frameworks. Pure mathematics. Production-ready.*
