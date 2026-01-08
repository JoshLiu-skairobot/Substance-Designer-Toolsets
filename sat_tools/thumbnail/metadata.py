"""
Thumbnail Metadata Module

Provides functionality to read and write metadata to PNG images
using PNG text chunks.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class ThumbnailMetadata:
    """Metadata embedded in a thumbnail image."""
    source_file: str
    graph_name: str
    generated_at: str
    resolution: Dict[str, int]
    parameter_hash: str = ""
    tags: List[str] = field(default_factory=list)
    custom_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'sourceFile': self.source_file,
            'graphName': self.graph_name,
            'generatedAt': self.generated_at,
            'resolution': self.resolution,
            'parameterHash': self.parameter_hash,
            'tags': self.tags,
        }
        if self.custom_data:
            data['customData'] = self.custom_data
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThumbnailMetadata':
        """Create from dictionary."""
        return cls(
            source_file=data.get('sourceFile', ''),
            graph_name=data.get('graphName', ''),
            generated_at=data.get('generatedAt', ''),
            resolution=data.get('resolution', {'width': 0, 'height': 0}),
            parameter_hash=data.get('parameterHash', ''),
            tags=data.get('tags', []),
            custom_data=data.get('customData'),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ThumbnailMetadata':
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def create(
        cls,
        source_file: str,
        graph_name: str,
        resolution: tuple,
        tags: Optional[List[str]] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> 'ThumbnailMetadata':
        """
        Create metadata for a new thumbnail.
        
        Args:
            source_file: Path to the source SBS/SBSAR file.
            graph_name: Name of the rendered graph.
            resolution: Tuple of (width, height).
            tags: Optional list of tags.
            custom_data: Optional custom data dictionary.
            
        Returns:
            New ThumbnailMetadata instance.
        """
        # Generate parameter hash from source file
        param_hash = ""
        try:
            with open(source_file, 'rb') as f:
                param_hash = hashlib.md5(f.read()).hexdigest()[:12]
        except Exception:
            param_hash = hashlib.md5(source_file.encode()).hexdigest()[:12]
        
        return cls(
            source_file=str(Path(source_file).name),
            graph_name=graph_name,
            generated_at=datetime.now().isoformat(),
            resolution={'width': resolution[0], 'height': resolution[1]},
            parameter_hash=param_hash,
            tags=tags or [],
            custom_data=custom_data,
        )


class MetadataWriter:
    """
    Writes metadata to PNG images.
    
    Uses PNG tEXt chunks to embed JSON metadata into images.
    """
    
    METADATA_KEY = 'SAT_Metadata'
    
    def __init__(self):
        """Initialize the writer."""
        self._has_pillow = False
        try:
            from PIL import Image, PngImagePlugin
            self._has_pillow = True
        except ImportError:
            pass
    
    def write(self, image_path: str, metadata: ThumbnailMetadata) -> bool:
        """
        Write metadata to a PNG image.
        
        Args:
            image_path: Path to the PNG image.
            metadata: Metadata to embed.
            
        Returns:
            True if successful.
        """
        if not self._has_pillow:
            raise ImportError("Pillow is required for metadata writing. Install with: pip install Pillow")
        
        from PIL import Image, PngImagePlugin
        
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if path.suffix.lower() != '.png':
            raise ValueError("Only PNG images are supported for metadata embedding")
        
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Create metadata
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text(self.METADATA_KEY, metadata.to_json())
            
            # Also add individual fields as separate chunks for compatibility
            pnginfo.add_text('SAT_SourceFile', metadata.source_file)
            pnginfo.add_text('SAT_GraphName', metadata.graph_name)
            pnginfo.add_text('SAT_GeneratedAt', metadata.generated_at)
            pnginfo.add_text('SAT_Tags', ','.join(metadata.tags))
            
            # Save with metadata
            img.save(image_path, 'PNG', pnginfo=pnginfo)
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to write metadata: {e}")
    
    def write_to_new_file(
        self, 
        source_image: str, 
        output_path: str, 
        metadata: ThumbnailMetadata
    ) -> str:
        """
        Create a new image with embedded metadata.
        
        Args:
            source_image: Path to source image.
            output_path: Path for output image.
            metadata: Metadata to embed.
            
        Returns:
            Path to the output image.
        """
        if not self._has_pillow:
            raise ImportError("Pillow is required. Install with: pip install Pillow")
        
        from PIL import Image, PngImagePlugin
        
        img = Image.open(source_image)
        
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text(self.METADATA_KEY, metadata.to_json())
        pnginfo.add_text('SAT_SourceFile', metadata.source_file)
        pnginfo.add_text('SAT_GraphName', metadata.graph_name)
        
        # Ensure output is PNG
        if not output_path.lower().endswith('.png'):
            output_path = str(Path(output_path).with_suffix('.png'))
        
        img.save(output_path, 'PNG', pnginfo=pnginfo)
        
        return output_path


class MetadataReader:
    """
    Reads metadata from PNG images.
    """
    
    METADATA_KEY = 'SAT_Metadata'
    
    def __init__(self):
        """Initialize the reader."""
        self._has_pillow = False
        try:
            from PIL import Image
            self._has_pillow = True
        except ImportError:
            pass
    
    def read(self, image_path: str) -> Optional[ThumbnailMetadata]:
        """
        Read metadata from a PNG image.
        
        Args:
            image_path: Path to the PNG image.
            
        Returns:
            ThumbnailMetadata if found, None otherwise.
        """
        if not self._has_pillow:
            raise ImportError("Pillow is required. Install with: pip install Pillow")
        
        from PIL import Image
        
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            img = Image.open(image_path)
            
            # Try to read the main metadata chunk
            if hasattr(img, 'info') and self.METADATA_KEY in img.info:
                json_str = img.info[self.METADATA_KEY]
                return ThumbnailMetadata.from_json(json_str)
            
            # Fallback: try to reconstruct from individual chunks
            if hasattr(img, 'info'):
                source_file = img.info.get('SAT_SourceFile', '')
                graph_name = img.info.get('SAT_GraphName', '')
                
                if source_file or graph_name:
                    return ThumbnailMetadata(
                        source_file=source_file,
                        graph_name=graph_name,
                        generated_at=img.info.get('SAT_GeneratedAt', ''),
                        resolution={'width': img.width, 'height': img.height},
                        tags=img.info.get('SAT_Tags', '').split(',') if img.info.get('SAT_Tags') else [],
                    )
            
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to read metadata: {e}")
    
    def has_metadata(self, image_path: str) -> bool:
        """
        Check if an image has SAT metadata.
        
        Args:
            image_path: Path to the image.
            
        Returns:
            True if metadata exists.
        """
        try:
            metadata = self.read(image_path)
            return metadata is not None
        except Exception:
            return False
