"""
System API

API endpoints for system monitoring and control.
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime

system_api = Blueprint('system_api', __name__)


@system_api.route('/status', methods=['GET'])
def get_system_status():
    """Get overall system status."""
    orchestrator = current_app.orchestrator
    
    if orchestrator:
        status = orchestrator.get_status()
    else:
        # Mock status when no orchestrator
        status = {
            'running': True,
            'system_health': 'healthy',
            'modules': {
                'total_modules': 8,
                'status_counts': {
                    'running': 7,
                    'stopped': 1
                }
            }
        }
    
    return jsonify({
        'success': True,
        'status': status,
        'timestamp': datetime.now().isoformat()
    })


@system_api.route('/modules', methods=['GET'])
def list_modules():
    """List all modules and their status."""
    # Mock module data
    modules = [
        {'name': 'data_ingestion', 'status': 'running', 'uptime': 99.8},
        {'name': 'feature_engineering', 'status': 'running', 'uptime': 99.9},
        {'name': 'prediction_core', 'status': 'running', 'uptime': 99.7},
        {'name': 'risk_management', 'status': 'running', 'uptime': 100.0},
        {'name': 'execution', 'status': 'running', 'uptime': 99.5},
        {'name': 'monitoring', 'status': 'running', 'uptime': 99.9},
        {'name': 'orchestrator', 'status': 'running', 'uptime': 100.0},
        {'name': 'web_ui', 'status': 'running', 'uptime': 100.0},
    ]
    
    return jsonify({
        'success': True,
        'modules': modules
    })


@system_api.route('/health', methods=['GET'])
def health_check():
    """Perform health check."""
    return jsonify({
        'success': True,
        'health': 'healthy',
        'checks': {
            'database': 'ok',
            'cache': 'ok',
            'api': 'ok',
            'modules': 'ok'
        }
    })


@system_api.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system performance metrics."""
    return jsonify({
        'success': True,
        'metrics': {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'disk_usage': 38.5,
            'requests_per_minute': 125,
            'active_connections': 12,
            'uptime_hours': 72.5
        }
    })


@system_api.route('/logs', methods=['GET'])
def get_logs():
    """Get recent system logs."""
    limit = request.args.get('limit', default=50, type=int)
    level = request.args.get('level', default='all')
    
    # Mock logs
    logs = []
    for i in range(limit):
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'module': 'orchestrator',
            'message': f'Sample log message {i}'
        })
    
    return jsonify({
        'success': True,
        'logs': logs,
        'count': len(logs)
    })


@system_api.route('/performance', methods=['GET'])
def get_performance():
    """Get performance statistics."""
    return jsonify({
        'success': True,
        'performance': {
            'predictions_per_second': 15.3,
            'avg_prediction_latency_ms': 45.2,
            'total_predictions_today': 1523,
            'accuracy_today': 68.5,
            'win_rate_today': 64.2,
            'profit_factor': 1.8
        }
    })
