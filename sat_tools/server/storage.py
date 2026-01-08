"""
Storage Service

Provides file storage functionality for uploaded assets.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


class StorageService:
    """
    Local file storage service for assets.
    """
    
    def __init__(
        self,
        base_path: str = "./storage",
        url_prefix: str = "/static/assets"
    ):
        """
        Initialize the storage service.
        
        Args:
            base_path: Base directory for file storage.
            url_prefix: URL prefix for accessing files.
        """
        # Always use absolute path for storage
        self.base_path = Path(base_path).resolve()
        self.url_prefix = url_prefix.rstrip('/')
        
        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_path(self, filename: str, asset_id: Optional[str] = None) -> Tuple[Path, str]:
        """
        Generate a storage path for a file.
        
        Args:
            filename: Original filename.
            asset_id: Optional asset ID for grouping.
            
        Returns:
            Tuple of (storage_path, url).
        """
        # Generate date-based directory structure
        now = datetime.utcnow()
        date_path = now.strftime("%Y/%m/%d")
        
        # Generate unique filename
        file_id = asset_id or str(uuid.uuid4())[:8]
        ext = Path(filename).suffix
        unique_name = f"{file_id}_{filename}"
        
        # Build paths (always use absolute path)
        rel_path = Path(date_path) / unique_name
        storage_path = (self.base_path / rel_path).resolve()
        url = f"{self.url_prefix}/{rel_path.as_posix()}"
        
        return storage_path, url
    
    def save_file(
        self,
        source_path: str,
        filename: Optional[str] = None,
        asset_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Save a file to storage.
        
        Args:
            source_path: Path to source file.
            filename: Optional filename override.
            asset_id: Optional asset ID for grouping.
            
        Returns:
            Tuple of (storage_path, url).
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        filename = filename or source.name
        storage_path, url = self._generate_path(filename, asset_id)
        
        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source, storage_path)
        
        return str(storage_path), url
    
    def save_uploaded_file(
        self,
        file_data: bytes,
        filename: str,
        asset_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Save uploaded file data to storage.
        
        Args:
            file_data: File content as bytes.
            filename: Filename.
            asset_id: Optional asset ID.
            
        Returns:
            Tuple of (storage_path, url).
        """
        storage_path, url = self._generate_path(filename, asset_id)
        
        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(storage_path, 'wb') as f:
            f.write(file_data)
        
        return str(storage_path), url
    
    def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            storage_path: Path to the file.
            
        Returns:
            True if deleted, False otherwise.
        """
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def get_file_path(self, url: str) -> Optional[str]:
        """
        Get the storage path for a URL.
        
        Args:
            url: Asset URL.
            
        Returns:
            Storage path or None.
        """
        if not url.startswith(self.url_prefix):
            return None
        
        rel_path = url[len(self.url_prefix):].lstrip('/')
        storage_path = self.base_path / rel_path
        
        if storage_path.exists():
            return str(storage_path)
        return None
    
    def cleanup_empty_dirs(self):
        """Remove empty directories in storage."""
        for dirpath, dirnames, filenames in os.walk(self.base_path, topdown=False):
            if not dirnames and not filenames:
                try:
                    os.rmdir(dirpath)
                except OSError:
                    pass
