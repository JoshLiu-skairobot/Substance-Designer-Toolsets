"""
SAT Server - Asset Repository Backend

This module provides the REST API backend for the asset repository,
including file storage and metadata management.
"""

from .app import create_app

__all__ = ['create_app']
__version__ = '1.0.0'
