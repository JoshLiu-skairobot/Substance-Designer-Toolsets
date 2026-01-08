"""
SAT Thumbnail Module - Thumbnail Generation for SBS/SBSAR Files

This module provides functionality to generate thumbnails from Substance
Designer files and embed metadata into the generated images.
"""

from .renderer import ThumbnailRenderer
from .metadata import ThumbnailMetadata, MetadataWriter, MetadataReader
from .batch import BatchProcessor

__all__ = [
    'ThumbnailRenderer',
    'ThumbnailMetadata',
    'MetadataWriter',
    'MetadataReader',
    'BatchProcessor'
]
__version__ = '1.0.0'
