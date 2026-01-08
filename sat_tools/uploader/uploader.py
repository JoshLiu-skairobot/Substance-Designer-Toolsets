"""
Asset Uploader Module

Provides functionality to upload baked textures to the asset repository.
"""

import os
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
import json


@dataclass
class UploadResult:
    """Result of an upload operation."""
    success: bool
    asset_id: str = ""
    asset_url: str = ""
    textures: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'assetId': self.asset_id,
            'url': self.asset_url,
            'textures': self.textures,
            'error': self.error
        }


class AssetUploader:
    """
    Uploads assets to the asset repository.
    
    Integrates with the asset repository backend API to upload
    baked textures and register them as assets.
    """
    
    def __init__(
        self,
        api_base_url: str = "http://localhost:5000/api",
        api_key: Optional[str] = None
    ):
        """
        Initialize the uploader.
        
        Args:
            api_base_url: Base URL for the asset repository API.
            api_key: Optional API key for authentication.
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self._session = requests.Session()
        
        if api_key:
            self._session.headers['Authorization'] = f'Bearer {api_key}'
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def upload_file(
        self,
        filepath: str,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> UploadResult:
        """
        Upload a single file to the repository.
        
        Args:
            filepath: Path to the file to upload.
            name: Optional name for the asset.
            tags: Optional list of tags.
            metadata: Optional metadata dictionary.
            progress_callback: Optional callback for upload progress.
            
        Returns:
            UploadResult with the operation result.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return UploadResult(
                success=False,
                error=f"File not found: {filepath}"
            )
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath.name, f, 'application/octet-stream')}
                data = {
                    'name': name or filepath.stem,
                    'tags': json.dumps(tags or []),
                    'metadata': json.dumps(metadata or {})
                }
                
                response = self._session.post(
                    f"{self.api_base_url}/assets/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                return UploadResult(
                    success=True,
                    asset_id=result.get('id', result.get('assetId', '')),
                    asset_url=result.get('url', ''),
                    textures=[{
                        'channel': filepath.stem.split('_')[-1] if '_' in filepath.stem else 'unknown',
                        'filename': filepath.name,
                        'url': result.get('url', '')
                    }]
                )
            else:
                return UploadResult(
                    success=False,
                    error=f"Upload failed: {response.status_code} - {response.text}"
                )
                
        except requests.exceptions.ConnectionError:
            return UploadResult(
                success=False,
                error=f"Connection error: Could not connect to {self.api_base_url}"
            )
        except Exception as e:
            return UploadResult(
                success=False,
                error=f"Upload failed: {str(e)}"
            )
    
    def upload_textures(
        self,
        files: List[str],
        name: str,
        source_file: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> UploadResult:
        """
        Upload multiple texture files as a single asset.
        
        Args:
            files: List of file paths to upload.
            name: Name for the asset.
            source_file: Original SBS/SBSAR file path.
            description: Optional description.
            tags: Optional list of tags.
            progress_callback: Optional callback (current, total, filename).
            
        Returns:
            UploadResult with the operation result.
        """
        # Validate files
        valid_files = []
        for f in files:
            path = Path(f)
            if path.exists():
                valid_files.append(path)
        
        if not valid_files:
            return UploadResult(
                success=False,
                error="No valid files to upload"
            )
        
        try:
            # Prepare multipart form data
            files_data = []
            for i, filepath in enumerate(valid_files):
                if progress_callback:
                    progress_callback(i + 1, len(valid_files), filepath.name)
                files_data.append(
                    ('files', (filepath.name, open(filepath, 'rb'), 'application/octet-stream'))
                )
            
            data = {
                'name': name,
                'sourceFile': source_file or '',
                'description': description or '',
                'tags': json.dumps(tags or [])
            }
            
            response = self._session.post(
                f"{self.api_base_url}/assets/upload-batch",
                files=files_data,
                data=data
            )
            
            # Close file handles
            for _, (_, fh, _) in files_data:
                fh.close()
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                textures = []
                for texture in result.get('textures', []):
                    textures.append({
                        'channel': texture.get('channel', ''),
                        'filename': texture.get('filename', ''),
                        'url': texture.get('url', '')
                    })
                
                return UploadResult(
                    success=True,
                    asset_id=result.get('id', result.get('assetId', '')),
                    asset_url=result.get('url', ''),
                    textures=textures
                )
            else:
                return UploadResult(
                    success=False,
                    error=f"Upload failed: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            return UploadResult(
                success=False,
                error=f"Upload failed: {str(e)}"
            )
    
    def upload_bake_result(
        self,
        bake_result: Dict[str, Any],
        name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> UploadResult:
        """
        Upload textures from a bake result.
        
        This is the callback handler for bake operations.
        
        Args:
            bake_result: Dictionary from BakeResult.to_dict().
            name: Optional name override.
            tags: Optional tags to add.
            
        Returns:
            UploadResult with the operation result.
        """
        if not bake_result.get('success'):
            return UploadResult(
                success=False,
                error=f"Cannot upload failed bake: {bake_result.get('error')}"
            )
        
        output_files = bake_result.get('outputFiles', [])
        if not output_files:
            return UploadResult(
                success=False,
                error="No output files in bake result"
            )
        
        source_file = bake_result.get('sourceFile', '')
        asset_name = name or Path(source_file).stem if source_file else 'Untitled Asset'
        
        return self.upload_textures(
            files=output_files,
            name=asset_name,
            source_file=source_file,
            tags=tags
        )
    
    def check_connection(self) -> bool:
        """
        Check if the API is reachable.
        
        Returns:
            True if connected.
        """
        try:
            response = self._session.get(
                f"{self.api_base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False


def create_upload_callback(
    uploader: AssetUploader,
    tags: Optional[List[str]] = None
) -> Callable[[Dict[str, Any]], None]:
    """
    Create a callback function for bake operations that uploads results.
    
    Args:
        uploader: AssetUploader instance.
        tags: Optional tags to apply.
        
    Returns:
        Callback function compatible with CallbackManager.
    """
    def callback(bake_result: Dict[str, Any]):
        result = uploader.upload_bake_result(bake_result, tags=tags)
        if result.success:
            print(f"Uploaded successfully: {result.asset_id} -> {result.asset_url}")
        else:
            print(f"Upload failed: {result.error}")
        return result
    
    return callback
