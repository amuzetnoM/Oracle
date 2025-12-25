"""
Data API

API endpoints for data operations.
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta

data_api = Blueprint('data_api', __name__)


@data_api.route('/providers', methods=['GET'])
def list_providers():
    """List available data providers."""
    providers = [
        {'name': 'FRED', 'status': 'active', 'type': 'economic'},
        {'name': 'Yahoo Finance', 'status': 'active', 'type': 'market'},
        {'name': 'Binance', 'status': 'active', 'type': 'crypto'},
        {'name': 'CoinGecko', 'status': 'active', 'type': 'crypto'},
    ]
    
    return jsonify({
        'success': True,
        'providers': providers
    })


@data_api.route('/fetch', methods=['POST'])
def fetch_data():
    """Fetch data for an asset."""
    data = request.get_json()
    asset = data.get('asset')
    provider = data.get('provider', 'yahoo')
    
    if not asset:
        return jsonify({
            'success': False,
            'error': 'Asset is required'
        }), 400
    
    # Mock response - in production, would call data ingestion module
    return jsonify({
        'success': True,
        'asset': asset,
        'provider': provider,
        'data_points': 100,
        'last_updated': datetime.now().isoformat()
    })


@data_api.route('/history/<asset>', methods=['GET'])
def get_history(asset):
    """Get historical data for an asset."""
    days = request.args.get('days', default=30, type=int)
    
    # Mock response
    return jsonify({
        'success': True,
        'asset': asset,
        'period': f'{days} days',
        'data_points': days,
        'start_date': (datetime.now() - timedelta(days=days)).isoformat(),
        'end_date': datetime.now().isoformat()
    })


@data_api.route('/status', methods=['GET'])
def data_status():
    """Get data ingestion status."""
    return jsonify({
        'success': True,
        'status': {
            'last_update': datetime.now().isoformat(),
            'providers_active': 4,
            'providers_total': 4,
            'cache_size_mb': 125.5,
            'requests_today': 1523
        }
    })
