"""
Batch Thumbnail Processing Module

Provides functionality for batch processing of thumbnail generation.
"""

import os
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from .renderer import ThumbnailRenderer, RenderResult
from .metadata import ThumbnailMetadata, MetadataWriter


@dataclass
class BatchResult:
    """Result of a batch processing operation."""
    total: int
    success: int
    failed: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)


class BatchProcessor:
    """
    Batch processor for thumbnail generation.
    
    Processes multiple SBS/SBSAR files and generates thumbnails
    with embedded metadata.
    """
    
    def __init__(
        self,
        sat_install_path: Optional[str] = None,
        max_workers: int = 4
    ):
        """
        Initialize the batch processor.
        
        Args:
            sat_install_path: Path to SAT installation.
            max_workers: Maximum number of parallel workers.
        """
        self.renderer = ThumbnailRenderer(sat_install_path)
        self.metadata_writer = MetadataWriter()
        self.max_workers = max_workers
    
    def find_files(
        self,
        directory: str,
        recursive: bool = False,
        extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Find Substance files in a directory.
        
        Args:
            directory: Directory to search.
            recursive: Whether to search recursively.
            extensions: File extensions to find. Defaults to ['.sbs', '.sbsar'].
            
        Returns:
            List of file paths.
        """
        if extensions is None:
            extensions = ['.sbs', '.sbsar']
        
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        files = []
        for ext in extensions:
            pattern = f'*{ext}'
            if recursive:
                files.extend(path.rglob(pattern))
            else:
                files.extend(path.glob(pattern))
        
        return sorted(files)
    
    def process_file(
        self,
        filepath: str,
        output_dir: str,
        resolution: int = 256,
        output_format: str = 'png',
        tags: Optional[List[str]] = None,
        embed_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single file.
        
        Args:
            filepath: Path to the SBS/SBSAR file.
            output_dir: Output directory for thumbnails.
            resolution: Output resolution.
            output_format: Output format.
            tags: Tags to embed in metadata.
            embed_metadata: Whether to embed metadata.
            
        Returns:
            Dictionary with processing result.
        """
        filepath = Path(filepath)
        
        # Render thumbnail
        output_path = Path(output_dir) / f"{filepath.stem}_preview.{output_format}"
        result = self.renderer.render(
            filepath=str(filepath),
            output_path=str(output_path),
            resolution=resolution,
            output_format=output_format
        )
        
        if not result.success:
            return {
                'success': False,
                'file': str(filepath),
                'error': result.error
            }
        
        # Embed metadata if requested and format is PNG
        if embed_metadata and output_format.lower() == 'png':
            try:
                metadata = ThumbnailMetadata.create(
                    source_file=str(filepath),
                    graph_name=result.graph_name,
                    resolution=result.resolution,
                    tags=tags or []
                )
                self.metadata_writer.write(result.output_path, metadata)
            except Exception as e:
                # Metadata failure shouldn't fail the whole operation
                return {
                    'success': True,
                    'file': str(filepath),
                    'output': result.output_path,
                    'metadata_error': str(e)
                }
        
        return {
            'success': True,
            'file': str(filepath),
            'output': result.output_path,
            'resolution': result.resolution
        }
    
    def process_directory(
        self,
        directory: str,
        output_dir: str,
        resolution: int = 256,
        output_format: str = 'png',
        recursive: bool = False,
        tags: Optional[List[str]] = None,
        embed_metadata: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> BatchResult:
        """
        Process all files in a directory.
        
        Args:
            directory: Directory containing SBS/SBSAR files.
            output_dir: Output directory for thumbnails.
            resolution: Output resolution.
            output_format: Output format.
            recursive: Whether to search recursively.
            tags: Tags to embed in metadata.
            embed_metadata: Whether to embed metadata.
            progress_callback: Optional callback for progress updates.
                              Called with (current, total, filename).
            
        Returns:
            BatchResult with processing summary.
        """
        # Find files
        files = self.find_files(directory, recursive)
        
        if not files:
            return BatchResult(total=0, success=0, failed=0)
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        errors = []
        success_count = 0
        failed_count = 0
        
        # Process files
        total = len(files)
        for i, filepath in enumerate(files):
            if progress_callback:
                progress_callback(i + 1, total, filepath.name)
            
            result = self.process_file(
                filepath=str(filepath),
                output_dir=output_dir,
                resolution=resolution,
                output_format=output_format,
                tags=tags,
                embed_metadata=embed_metadata
            )
            
            if result['success']:
                success_count += 1
                results.append(result)
            else:
                failed_count += 1
                errors.append({
                    'file': result['file'],
                    'error': result.get('error', 'Unknown error')
                })
        
        return BatchResult(
            total=total,
            success=success_count,
            failed=failed_count,
            results=results,
            errors=errors
        )
    
    def process_parallel(
        self,
        files: List[str],
        output_dir: str,
        resolution: int = 256,
        output_format: str = 'png',
        tags: Optional[List[str]] = None,
        embed_metadata: bool = True
    ) -> BatchResult:
        """
        Process files in parallel.
        
        Args:
            files: List of file paths.
            output_dir: Output directory.
            resolution: Output resolution.
            output_format: Output format.
            tags: Tags to embed.
            embed_metadata: Whether to embed metadata.
            
        Returns:
            BatchResult with processing summary.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self.process_file,
                    filepath=f,
                    output_dir=output_dir,
                    resolution=resolution,
                    output_format=output_format,
                    tags=tags,
                    embed_metadata=embed_metadata
                ): f for f in files
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        results.append(result)
                    else:
                        errors.append({
                            'file': result['file'],
                            'error': result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    errors.append({
                        'file': futures[future],
                        'error': str(e)
                    })
        
        return BatchResult(
            total=len(files),
            success=len(results),
            failed=len(errors),
            results=results,
            errors=errors
        )
