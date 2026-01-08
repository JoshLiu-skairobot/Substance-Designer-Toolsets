"""
Texture Baker Module

Provides functionality to bake textures from SBS/SBSAR files
using sbsrender command-line tool.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats."""
    PNG = "png"
    TGA = "tga"
    TIFF = "tiff"
    JPG = "jpg"
    EXR = "exr"


@dataclass
class BakeConfig:
    """Configuration for texture baking."""
    resolution: int = 2048
    output_format: OutputFormat = OutputFormat.PNG
    output_dir: str = ""
    channels: Optional[List[str]] = None  # None means all outputs
    parameters: Optional[Dict[str, Any]] = None  # Custom parameter values
    bit_depth: int = 8  # 8 or 16
    
    # Common output channel names
    DEFAULT_CHANNELS = [
        'basecolor', 'diffuse', 'albedo',
        'normal', 'height', 'displacement',
        'roughness', 'glossiness',
        'metallic', 'metalness',
        'ambientocclusion', 'ao',
        'opacity', 'emissive'
    ]


@dataclass
class BakeResult:
    """Result of a bake operation."""
    success: bool
    source_file: str
    output_files: List[str] = field(default_factory=list)
    output_dir: str = ""
    resolution: int = 0
    error: Optional[str] = None
    duration_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'sourceFile': self.source_file,
            'outputFiles': self.output_files,
            'outputDir': self.output_dir,
            'resolution': self.resolution,
            'error': self.error,
            'durationMs': self.duration_ms
        }


class TextureBaker:
    """
    Bakes textures from SBS/SBSAR files.
    
    Uses sbsrender to generate full texture sets from Substance files.
    """
    
    def __init__(self, sat_install_path: Optional[str] = None):
        """
        Initialize the baker.
        
        Args:
            sat_install_path: Path to SAT installation.
        """
        self.sat_path = sat_install_path or self._detect_sat_path()
        self.sbsrender_path = self._find_sbsrender()
        
    def _detect_sat_path(self) -> Optional[str]:
        """Detect SAT installation path."""
        possible_paths = [
            r"C:\Program Files\Adobe\Adobe Substance 3D Automation Toolkit",
            r"C:\Program Files\Allegorithmic\Substance Automation Toolkit",
            "/opt/Adobe/Adobe_Substance_3D_Automation_Toolkit",
            str(Path(__file__).parent.parent.parent / 
                "Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _find_sbsrender(self) -> Optional[str]:
        """Find the sbsrender executable."""
        if self.sat_path is None:
            return None
            
        candidates = [
            os.path.join(self.sat_path, 'sbsrender.exe'),
            os.path.join(self.sat_path, 'sbsrender'),
            os.path.join(self.sat_path, 'bin', 'sbsrender.exe'),
            os.path.join(self.sat_path, 'bin', 'sbsrender'),
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
                
        return None
    
    def get_available_outputs(self, filepath: str) -> List[str]:
        """
        Get list of available outputs from an SBS/SBSAR file.
        
        Args:
            filepath: Path to the file.
            
        Returns:
            List of output names.
        """
        if self.sbsrender_path is None:
            return []
            
        cmd = [
            self.sbsrender_path,
            'info',
            '--input', str(filepath),
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            outputs = []
            if result.returncode == 0:
                # Parse output to find available outputs
                in_outputs = False
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'OUTPUT' in line.upper() or 'Outputs:' in line:
                        in_outputs = True
                        continue
                    if in_outputs and line:
                        # Extract output name
                        if ':' in line:
                            outputs.append(line.split(':')[0].strip())
                        elif line and not line.startswith('-'):
                            outputs.append(line)
            return outputs
        except Exception:
            return []
    
    def bake(
        self,
        filepath: str,
        config: Optional[BakeConfig] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> BakeResult:
        """
        Bake textures from an SBS/SBSAR file.
        
        Args:
            filepath: Path to the SBS/SBSAR file.
            config: Bake configuration. If None, uses defaults.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            BakeResult with the operation result.
        """
        import time
        start_time = time.time()
        
        if self.sbsrender_path is None:
            return BakeResult(
                success=False,
                source_file=filepath,
                error="sbsrender not found. Check SAT installation path."
            )
        
        filepath = Path(filepath)
        if not filepath.exists():
            return BakeResult(
                success=False,
                source_file=str(filepath),
                error=f"File not found: {filepath}"
            )
        
        config = config or BakeConfig()
        
        # Determine output directory
        if config.output_dir:
            output_dir = Path(config.output_dir)
        else:
            output_dir = filepath.parent / f"{filepath.stem}_textures"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get channels to render
        channels = config.channels or self.get_available_outputs(str(filepath))
        if not channels:
            channels = config.DEFAULT_CHANNELS
        
        output_files = []
        errors = []
        
        for channel in channels:
            if progress_callback:
                progress_callback(f"Baking {channel}...")
            
            output_file = output_dir / f"{filepath.stem}_{channel}.{config.output_format.value}"
            
            cmd = [
                self.sbsrender_path,
                'render',
                '--input', str(filepath),
                '--output-path', str(output_dir),
                '--output-name', f"{filepath.stem}_{channel}",
                '--output-format', config.output_format.value,
                '--set-value', f'$outputsize@{config.resolution},{config.resolution}',
                '--input-graph-output', channel,
            ]
            
            # Add custom parameters
            if config.parameters:
                for key, value in config.parameters.items():
                    cmd.extend(['--set-value', f'{key}@{value}'])
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per output
                )
                
                if result.returncode == 0:
                    # Check if output file was created
                    if output_file.exists():
                        output_files.append(str(output_file))
                    else:
                        # Try to find the actual output file
                        pattern = f"{filepath.stem}_{channel}*.{config.output_format.value}"
                        found = list(output_dir.glob(pattern))
                        if found:
                            output_files.extend([str(f) for f in found])
                else:
                    # Don't treat missing outputs as errors
                    if 'not found' not in result.stderr.lower():
                        errors.append(f"{channel}: {result.stderr}")
                        
            except subprocess.TimeoutExpired:
                errors.append(f"{channel}: Render timed out")
            except Exception as e:
                errors.append(f"{channel}: {str(e)}")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if output_files:
            return BakeResult(
                success=True,
                source_file=str(filepath),
                output_files=output_files,
                output_dir=str(output_dir),
                resolution=config.resolution,
                duration_ms=duration_ms,
                error='; '.join(errors) if errors else None
            )
        else:
            return BakeResult(
                success=False,
                source_file=str(filepath),
                output_dir=str(output_dir),
                error='; '.join(errors) if errors else "No outputs generated",
                duration_ms=duration_ms
            )
    
    def bake_single_output(
        self,
        filepath: str,
        output_name: str,
        output_path: str,
        resolution: int = 2048,
        output_format: OutputFormat = OutputFormat.PNG
    ) -> BakeResult:
        """
        Bake a single output from an SBS/SBSAR file.
        
        Args:
            filepath: Path to the source file.
            output_name: Name of the output to bake.
            output_path: Path for the output file.
            resolution: Output resolution.
            output_format: Output format.
            
        Returns:
            BakeResult with the operation result.
        """
        config = BakeConfig(
            resolution=resolution,
            output_format=output_format,
            output_dir=str(Path(output_path).parent),
            channels=[output_name]
        )
        return self.bake(filepath, config)
