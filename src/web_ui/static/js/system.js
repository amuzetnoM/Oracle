// System Monitor JavaScript

const { fetchAPI, formatNumber, startAutoRefresh } = window.OracleUtils;

// Load system status
async function loadSystemStatus() {
    try {
        const data = await fetchAPI('/api/system/status');
        
        if (data.success) {
            const health = data.status.system_health;
            const healthIndicator = document.getElementById('healthIndicator');
            const healthText = document.getElementById('healthText');
            
            healthText.textContent = health.toUpperCase();
            healthIndicator.className = 'health-indicator ' + 
                (health === 'healthy' ? 'text-success' : 
                 health === 'degraded' ? 'text-warning' : 'text-danger');
        }
    } catch (error) {
        console.error('Error loading system status:', error);
    }
}

// Load modules status
async function loadModules() {
    try {
        const data = await fetchAPI('/api/system/modules');
        const container = document.getElementById('modulesList');
        
        if (data.success && data.modules.length > 0) {
            container.innerHTML = data.modules.map(module => {
                const statusClass = module.status === 'running' ? 'text-success' : 'text-danger';
                return `
                    <div class="module-item">
                        <div><strong>${module.name}</strong></div>
                        <div class="${statusClass}">${module.status.toUpperCase()}</div>
                        <div>Uptime: ${formatNumber(module.uptime, 1)}%</div>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        document.getElementById('modulesList').innerHTML = 
            '<div class="text-danger">Error loading modules</div>';
    }
}

// Load resource usage
async function loadResourceUsage() {
    try {
        const data = await fetchAPI('/api/system/metrics');
        
        if (data.success) {
            const metrics = data.metrics;
            
            // Update CPU
            document.getElementById('cpuUsage').style.width = metrics.cpu_usage + '%';
            document.getElementById('cpuPercent').textContent = 
                formatNumber(metrics.cpu_usage, 1) + '%';
            
            // Update Memory
            document.getElementById('memUsage').style.width = metrics.memory_usage + '%';
            document.getElementById('memPercent').textContent = 
                formatNumber(metrics.memory_usage, 1) + '%';
        }
    } catch (error) {
        console.error('Error loading resource usage:', error);
    }
}

// Load system logs
async function loadLogs() {
    try {
        const data = await fetchAPI('/api/system/logs?limit=20');
        const container = document.getElementById('systemLogs');
        
        if (data.success && data.logs.length > 0) {
            container.innerHTML = data.logs.map(log => `
                <div class="log-entry">
                    <span class="log-level">[${log.level}]</span>
                    <span class="log-module">${log.module}:</span>
                    <span>${log.message}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        document.getElementById('systemLogs').innerHTML = 
            '<div class="text-danger">Error loading logs</div>';
    }
}

// Load performance stats
async function loadPerformanceStats() {
    try {
        const data = await fetchAPI('/api/system/performance');
        const container = document.getElementById('perfStats');
        
        if (data.success) {
            const perf = data.performance;
            container.innerHTML = `
                <div class="stat-item">
                    Predictions/sec: <strong>${formatNumber(perf.predictions_per_second, 1)}</strong>
                </div>
                <div class="stat-item">
                    Avg Latency: <strong>${formatNumber(perf.avg_prediction_latency_ms, 1)}ms</strong>
                </div>
                <div class="stat-item">
                    Today's Predictions: <strong>${perf.total_predictions_today}</strong>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('perfStats').innerHTML = 
            '<div class="text-danger">Error loading stats</div>';
    }
}

// Initialize system monitor
if (document.getElementById('healthIndicator')) {
    loadSystemStatus();
    loadModules();
    loadResourceUsage();
    loadLogs();
    loadPerformanceStats();
    
    // Auto-refresh every 5 seconds
    startAutoRefresh(() => {
        loadSystemStatus();
        loadModules();
        loadResourceUsage();
        loadPerformanceStats();
    }, 5000);
}
