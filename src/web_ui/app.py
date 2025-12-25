"""
Flask Application

Main Flask application for the web UI.
"""

from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO
import logging

# Import API blueprints
from .api.data_api import data_api
from .api.prediction_api import prediction_api
from .api.system_api import system_api


def create_app(orchestrator=None):
    """
    Create and configure Flask application.
    
    Args:
        orchestrator: Optional Orchestrator instance
    
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['DEBUG'] = True
    
    # Enable CORS
    CORS(app)
    
    # Initialize SocketIO for real-time updates
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Store orchestrator reference
    app.orchestrator = orchestrator
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Register blueprints
    app.register_blueprint(data_api, url_prefix='/api/data')
    app.register_blueprint(prediction_api, url_prefix='/api/prediction')
    app.register_blueprint(system_api, url_prefix='/api/system')
    
    # Main routes
    @app.route('/')
    def index():
        """Main dashboard page."""
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard view."""
        return render_template('dashboard.html')
    
    @app.route('/system')
    def system_monitor():
        """System monitoring view."""
        return render_template('system_monitor.html')
    
    # WebSocket events
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        app.logger.info('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        app.logger.info('Client disconnected')
    
    @socketio.on('subscribe_updates')
    def handle_subscribe(data):
        """Handle subscription to updates."""
        app.logger.info(f'Client subscribed to: {data}')
    
    # Store socketio instance
    app.socketio = socketio
    
    return app


def run_app(host='0.0.0.0', port=5000, orchestrator=None):
    """
    Run the Flask application.
    
    Args:
        host: Host address
        port: Port number
        orchestrator: Orchestrator instance
    """
    app = create_app(orchestrator)
    app.socketio.run(app, host=host, port=port, debug=True)
