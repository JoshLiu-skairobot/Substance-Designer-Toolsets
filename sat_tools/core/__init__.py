"""
SAT Core Module - Texture Baking and Processing

This module provides core functionality for baking textures
from SBS/SBSAR files using the Substance Automation Toolkit.
"""

from .baker import TextureBaker, BakeResult, BakeConfig
from .callback import CallbackManager, BakeCallback

__all__ = [
    'TextureBaker',
    'BakeResult',
    'BakeConfig',
    'CallbackManager',
    'BakeCallback'
]
__version__ = '1.0.0'
