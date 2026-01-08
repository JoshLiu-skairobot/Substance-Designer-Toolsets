"""
Flask Application Factory

Creates and configures the Flask application for the asset repository.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .models import Database
from .storage import StorageService
from .routes import assets_bp, parameters_bp, thumbnails_bp


def setup_logging(app: Flask):
    """Setup logging configuration."""
    # Create logs directory
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / 'sat_server.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure Flask logger
    app.logger.setLevel(logging.DEBUG)
    
    logging.info("Logging system initialized")


def create_app(config: dict = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary.
        
    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    
    # Setup logging first
    setup_logging(app)
    
    logging.info("Creating Flask application")
    
    # Default configuration
    base_path = Path(__file__).parent.parent
    app.config['DATABASE_PATH'] = str(base_path / 'assets.db')
    app.config['STORAGE_PATH'] = str(base_path / 'storage')
    app.config['STATIC_URL_PREFIX'] = '/static/assets'
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
    
    # Override with provided config
    if config:
        app.config.update(config)
    
    logging.info(f"Database path: {app.config['DATABASE_PATH']}")
    logging.info(f"Storage path: {app.config['STORAGE_PATH']}")
    
    # Enable CORS
    CORS(app, origins=['http://localhost:5173', 'http://localhost:3000'])
    
    # Initialize database
    db_path = app.config['DATABASE_PATH']
    app.config['database'] = Database(db_path)
    logging.info("Database initialized")
    
    # Initialize storage
    storage_path = app.config['STORAGE_PATH']
    url_prefix = app.config['STATIC_URL_PREFIX']
    app.config['storage'] = StorageService(storage_path, url_prefix)
    logging.info("Storage service initialized")
    
    # Register blueprints
    app.register_blueprint(assets_bp)
    app.register_blueprint(parameters_bp)
    app.register_blueprint(thumbnails_bp)
    logging.info("Blueprints registered")
    
    # Health check endpoint
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0'
        })
    
    # Serve static files (uploaded assets)
    @app.route('/static/assets/<path:filename>')
    def serve_asset(filename):
        storage = app.config['storage']
        logging.debug(f"Serving asset: {filename}")
        return send_from_directory(storage.base_path, filename)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        logging.warning(f"404 Not Found: {e}")
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"500 Server Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def request_too_large(e):
        logging.warning(f"413 Request Too Large: {e}")
        return jsonify({'error': 'File too large'}), 413
    
    logging.info("Flask application created successfully")
    return app


def run_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """
    Run the development server.
    
    Args:
        host: Host to bind to.
        port: Port to bind to.
        debug: Enable debug mode.
    """
    app = create_app()
    logging.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
