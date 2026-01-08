"""
SAT Tools - Substance Automation Toolkit Tools

A comprehensive toolkit for working with Substance Designer files,
including parameter extraction, thumbnail generation, texture baking,
and asset repository management.

Modules:
    - extractor: Extract parameters from SBS/SBSAR files
    - thumbnail: Generate thumbnails with metadata
    - core: Texture baking functionality
    - uploader: Asset upload service
    - server: REST API backend
"""

__version__ = '1.0.0'
__author__ = 'SAT Tools Team'

from .extractor import SBSParser, ParameterExtractor, ParameterSchema
from .thumbnail import ThumbnailRenderer, ThumbnailMetadata, BatchProcessor
from .core import TextureBaker, BakeResult, CallbackManager
from .uploader import AssetUploader, UploadResult

__all__ = [
    # Extractor
    'SBSParser',
    'ParameterExtractor',
    'ParameterSchema',
    # Thumbnail
    'ThumbnailRenderer',
    'ThumbnailMetadata',
    'BatchProcessor',
    # Core
    'TextureBaker',
    'BakeResult',
    'CallbackManager',
    # Uploader
    'AssetUploader',
    'UploadResult',
]
