"""
API Routes

Defines Flask blueprints for the REST API.
"""

from .assets import assets_bp
from .parameters import parameters_bp
from .thumbnails import thumbnails_bp

__all__ = ['assets_bp', 'parameters_bp', 'thumbnails_bp']
