// Dashboard JavaScript

const { fetchAPI, postAPI, formatNumber, formatTimestamp, startAutoRefresh } = window.OracleUtils;

// Make prediction
document.getElementById('predictionForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const asset = document.getElementById('assetInput').value;
    const resultBox = document.getElementById('predictionResult');
    
    resultBox.innerHTML = '<div class="loading">Making prediction...</div>';
    
    try {
        const data = await postAPI('/api/prediction/predict', { asset });
        
        if (data.success) {
            const pred = data.prediction;
            const directionClass = pred.prediction === 'up' ? 'text-success' : 
                                  pred.prediction === 'down' ? 'text-danger' : '';
            
            resultBox.innerHTML = `
                <div class="prediction-result">
                    <h4>${pred.asset}</h4>
                    <div class="prediction-direction ${directionClass}">
                        ${pred.prediction.toUpperCase()}
                    </div>
                    <div class="confidence">
                        Confidence: ${formatNumber(pred.confidence * 100, 1)}%
                    </div>
                    <div class="timestamp">
                        ${formatTimestamp(pred.timestamp)}
                    </div>
                </div>
            `;
        }
    } catch (error) {
        resultBox.innerHTML = '<div class="text-danger">Error making prediction</div>';
    }
});

// Load performance metrics
async function loadMetrics() {
    try {
        const perfData = await fetchAPI('/api/system/performance');
        if (perfData.success) {
            const perf = perfData.performance;
            document.getElementById('metricAccuracy').textContent = 
                formatNumber(perf.accuracy_today, 1) + '%';
            document.getElementById('metricWinRate').textContent = 
                formatNumber(perf.win_rate_today, 1) + '%';
            document.getElementById('metricProfitFactor').textContent = 
                formatNumber(perf.profit_factor, 2);
            document.getElementById('metricPredictions').textContent = 
                perf.total_predictions_today;
        }
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

// Load recent predictions
async function loadRecentPredictions() {
    try {
        const data = await fetchAPI('/api/prediction/recent?limit=10');
        const container = document.getElementById('recentPredictions');
        
        if (data.success && data.predictions.length > 0) {
            container.innerHTML = data.predictions.map(pred => {
                const outcomeClass = pred.outcome === 'correct' ? 'text-success' : 
                                    pred.outcome === 'incorrect' ? 'text-danger' : '';
                
                return `
                    <div class="prediction-item">
                        <strong>${pred.asset}</strong> - 
                        <span class="${outcomeClass}">${pred.prediction.toUpperCase()}</span>
                        (${formatNumber(pred.confidence * 100, 0)}%)
                        <span class="${outcomeClass}">${pred.outcome}</span>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<div>No predictions yet</div>';
        }
    } catch (error) {
        document.getElementById('recentPredictions').innerHTML = 
            '<div class="text-danger">Error loading predictions</div>';
    }
}

// Load data providers
async function loadProviders() {
    try {
        const data = await fetchAPI('/api/data/providers');
        const container = document.getElementById('dataProviders');
        
        if (data.success && data.providers.length > 0) {
            container.innerHTML = data.providers.map(provider => `
                <div class="provider-item">
                    <span>${provider.name}</span>
                    <span class="text-success">✓ ${provider.status}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        document.getElementById('dataProviders').innerHTML = 
            '<div class="text-danger">Error loading providers</div>';
    }
}

// Initialize dashboard
if (document.getElementById('predictionForm')) {
    loadMetrics();
    loadRecentPredictions();
    loadProviders();
    
    // Auto-refresh predictions every 10 seconds
    startAutoRefresh(() => {
        loadRecentPredictions();
        loadMetrics();
    }, 10000);
}
