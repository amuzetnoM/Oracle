// Main JavaScript for Syndicate Web UI

// Utility functions
function formatNumber(num, decimals = 2) {
    return num.toFixed(decimals);
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

function showError(message) {
    console.error(message);
    alert(message);
}

// API helper
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function postAPI(endpoint, data) {
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auto-refresh functionality
let autoRefreshInterval;

function startAutoRefresh(callback, intervalMs = 5000) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    callback(); // Initial call
    autoRefreshInterval = setInterval(callback, intervalMs);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Export utilities
window.SyndicateUtils = {
    formatNumber,
    formatTimestamp,
    showError,
    fetchAPI,
    postAPI,
    startAutoRefresh,
    stopAutoRefresh
};
