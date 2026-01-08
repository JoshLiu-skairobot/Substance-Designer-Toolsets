"""
Thumbnail Renderer Module

Provides functionality to render thumbnails from SBS/SBSAR files
using sbsrender command-line tool.
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GraphOutput:
    """Represents an output of a graph."""
    name: str
    usage: str  # e.g., 'baseColor', 'normal', 'roughness'


@dataclass
class GraphInfo:
    """Information about a graph in an SBSAR file."""
    url: str  # Full URL like 'pkg://ABB_product_test_mod'
    name: str  # Just the graph name
    inputs: List[str] = field(default_factory=list)
    outputs: List[GraphOutput] = field(default_factory=list)


@dataclass
class RenderResult:
    """Result of a thumbnail render operation."""
    success: bool
    output_path: str
    graph_name: str
    resolution: tuple
    error: Optional[str] = None


class ThumbnailRenderer:
    """
    Renders thumbnails from SBS/SBSAR files using sbsrender.
    
    Uses the Substance Automation Toolkit's sbsrender command to
    generate preview images of Substance materials.
    
    Note: SBS files must be compiled to SBSAR first using sbscooker.
    """
    
    def __init__(self, sat_install_path: Optional[str] = None):
        """
        Initialize the renderer.
        
        Args:
            sat_install_path: Path to SAT installation. If None, will try to detect.
        """
        self.sat_path = sat_install_path or self._detect_sat_path()
        self.sbsrender_path = self._find_tool('sbsrender')
        self.sbscooker_path = self._find_tool('sbscooker')
        
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
    
    def _find_tool(self, tool_name: str) -> Optional[str]:
        """Find a SAT tool executable."""
        if self.sat_path is None:
            return None
        
        # Windows executables
        exe_name = f"{tool_name}.exe" if os.name == 'nt' else tool_name
            
        # Check common locations
        candidates = [
            os.path.join(self.sat_path, exe_name),
            os.path.join(self.sat_path, 'bin', exe_name),
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
                
        return None
    
    def get_graph_info(self, sbsar_path: str) -> List[GraphInfo]:
        """
        Parse sbsrender info output to get graph information.
        
        Args:
            sbsar_path: Path to the SBSAR file.
            
        Returns:
            List of GraphInfo objects.
        """
        if self.sbsrender_path is None:
            return []
        
        cmd = [
            self.sbsrender_path,
            'info',
            '--input', sbsar_path,
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"sbsrender info failed: {result.stderr}")
                return []
            
            return self._parse_graph_info(result.stdout)
            
        except Exception as e:
            logger.exception(f"Error getting graph info: {e}")
            return []
    
    def _parse_graph_info(self, info_output: str) -> List[GraphInfo]:
        """
        Parse the output of sbsrender info.
        
        Example output:
        GRAPH-URL pkg://ABB_product_test_mod
          INPUT $time FLOAT1
          OUTPUT basecolor baseColor
          OUTPUT normal normal
        """
        graphs: List[GraphInfo] = []
        current_graph: Optional[GraphInfo] = None
        
        for line in info_output.splitlines():
            line = line.strip()
            
            # Match graph URL
            if line.startswith('GRAPH-URL'):
                if current_graph:
                    graphs.append(current_graph)
                
                url = line.replace('GRAPH-URL', '').strip()
                # Extract graph name from URL like 'pkg://GraphName'
                name = url.replace('pkg://', '') if url.startswith('pkg://') else url
                current_graph = GraphInfo(url=url, name=name)
                
            elif current_graph:
                # Match INPUT
                if line.startswith('INPUT'):
                    parts = line.split()
                    if len(parts) >= 2:
                        current_graph.inputs.append(parts[1])
                
                # Match OUTPUT
                elif line.startswith('OUTPUT'):
                    parts = line.split()
                    if len(parts) >= 3:
                        output_name = parts[1]
                        output_usage = parts[2]
                        current_graph.outputs.append(GraphOutput(
                            name=output_name,
                            usage=output_usage
                        ))
        
        # Don't forget the last graph
        if current_graph:
            graphs.append(current_graph)
        
        return graphs
    
    def find_best_graph(self, graphs: List[GraphInfo]) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the best graph to render for a thumbnail.
        
        Looks for a graph that has a basecolor/diffuse/albedo output.
        
        Args:
            graphs: List of GraphInfo objects.
            
        Returns:
            Tuple of (graph_name, output_name) or (None, None) if not found.
        """
        # Priority list of output names/usages for thumbnail
        priority_outputs = [
            'basecolor', 'baseColor', 'diffuse', 'albedo',
            'Base_Color', 'base_color', 'Diffuse', 'Albedo'
        ]
        
        for graph in graphs:
            # Skip graphs with no outputs
            if not graph.outputs:
                continue
            
            # Look for priority outputs
            for priority in priority_outputs:
                for output in graph.outputs:
                    if output.name.lower() == priority.lower() or \
                       output.usage.lower() == priority.lower():
                        logger.info(f"Found best graph: {graph.name} with output: {output.name}")
                        return graph.name, output.name
        
        # Fallback: return first graph with any outputs
        for graph in graphs:
            if graph.outputs:
                logger.info(f"Using fallback graph: {graph.name} with output: {graph.outputs[0].name}")
                return graph.name, graph.outputs[0].name
        
        return None, None
    
    def cook_sbs(
        self,
        sbs_path: str,
        output_path: Optional[str] = None
    ) -> tuple:
        """
        Cook/compile an SBS file to SBSAR.
        
        Args:
            sbs_path: Path to the SBS file.
            output_path: Optional output path. If None, uses temp directory.
            
        Returns:
            Tuple of (success, sbsar_path, error_message)
        """
        if self.sbscooker_path is None:
            return False, '', "sbscooker not found. Check SAT installation path."
        
        sbs_file = Path(sbs_path)
        if not sbs_file.exists():
            return False, '', f"SBS file not found: {sbs_path}"
        
        # Determine output path
        if output_path is None:
            output_dir = tempfile.mkdtemp(prefix='sat_cook_')
            sbsar_path = os.path.join(output_dir, f"{sbs_file.stem}.sbsar")
        else:
            sbsar_path = output_path
            Path(sbsar_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Build sbscooker command
        cmd = [
            self.sbscooker_path,
            '--inputs', str(sbs_file),
            '--output-path', str(Path(sbsar_path).parent),
            '--output-name', sbs_file.stem,
        ]
        
        logger.info(f"Cooking SBS: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for cooking
            )
            
            if result.returncode == 0:
                # Check if output file exists
                if Path(sbsar_path).exists():
                    logger.info(f"Successfully cooked to: {sbsar_path}")
                    return True, sbsar_path, None
                else:
                    return False, '', f"SBSAR file not created: {sbsar_path}"
            else:
                logger.error(f"sbscooker failed: {result.stderr}")
                return False, '', f"sbscooker failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, '', "Cooking timed out after 300 seconds"
        except Exception as e:
            return False, '', f"Cooking failed: {str(e)}"
    
    def render(
        self,
        filepath: str,
        output_path: Optional[str] = None,
        resolution: int = 256,
        output_format: str = 'png',
        graph_name: Optional[str] = None,
        output_name: str = 'basecolor'
    ) -> RenderResult:
        """
        Render a thumbnail from an SBS/SBSAR file.
        
        Args:
            filepath: Path to the SBS/SBSAR file.
            output_path: Output path for the thumbnail. If None, uses temp directory.
            resolution: Output resolution (e.g., 256 for 256x256).
            output_format: Output format ('png' or 'jpg').
            graph_name: Name of the graph to render. If None, auto-detects best graph.
            output_name: Name of the output to render (e.g., 'basecolor').
            
        Returns:
            RenderResult with the operation result.
        """
        if self.sbsrender_path is None:
            return RenderResult(
                success=False,
                output_path='',
                graph_name=graph_name or '',
                resolution=(resolution, resolution),
                error="sbsrender not found. Check SAT installation path."
            )
        
        filepath = Path(filepath)
        if not filepath.exists():
            return RenderResult(
                success=False,
                output_path='',
                graph_name=graph_name or '',
                resolution=(resolution, resolution),
                error=f"File not found: {filepath}"
            )
        
        # If it's an SBS file, cook it first
        render_file = str(filepath)
        temp_sbsar = None
        temp_sbsar_dir = None
        
        if filepath.suffix.lower() == '.sbs':
            logger.info(f"Cooking SBS file: {filepath}")
            success, sbsar_path, error = self.cook_sbs(str(filepath))
            if not success:
                return RenderResult(
                    success=False,
                    output_path='',
                    graph_name=graph_name or '',
                    resolution=(resolution, resolution),
                    error=f"Failed to cook SBS file: {error}"
                )
            render_file = sbsar_path
            temp_sbsar = sbsar_path
            temp_sbsar_dir = str(Path(sbsar_path).parent)
        
        # Auto-detect graph and output if not specified
        if graph_name is None:
            logger.info("No graph specified, auto-detecting best graph...")
            graphs = self.get_graph_info(render_file)
            if graphs:
                detected_graph, detected_output = self.find_best_graph(graphs)
                if detected_graph:
                    graph_name = detected_graph
                    output_name = detected_output or output_name
                    logger.info(f"Auto-selected graph: {graph_name}, output: {output_name}")
                else:
                    logger.warning("No suitable graph found, using default behavior")
            else:
                logger.warning("Could not get graph info, using default behavior")
        
        # Determine output path
        if output_path is None:
            output_dir = tempfile.mkdtemp(prefix='sat_thumbnail_')
            output_path = os.path.join(
                output_dir, 
                f"{filepath.stem}_preview.{output_format}"
            )
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert pixel resolution to log2 value for Substance
        # 256 -> 8, 512 -> 9, 1024 -> 10, 2048 -> 11, 4096 -> 12
        import math
        log2_res = int(math.log2(resolution)) if resolution > 0 else 8
        # Clamp to valid range (5 = 32px to 13 = 8192px)
        log2_res = max(5, min(13, log2_res))
        
        # Build sbsrender command
        cmd = [
            self.sbsrender_path,
            'render',
            '--input', render_file,
            '--output-path', str(Path(output_path).parent),
            '--output-name', f"{filepath.stem}_preview",
            '--output-format', output_format,
            '--set-value', f'$outputsize@{log2_res},{log2_res}',
        ]
        
        if graph_name:
            cmd.extend(['--input-graph', graph_name])
            
        # Add output selection
        cmd.extend(['--input-graph-output', output_name])
        
        logger.info(f"Rendering: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                # Find the actual output file
                output_dir = Path(output_path).parent
                expected_name = f"{filepath.stem}_preview.{output_format}"
                actual_output = output_dir / expected_name
                
                if actual_output.exists():
                    logger.info(f"Thumbnail rendered successfully: {actual_output}")
                    return RenderResult(
                        success=True,
                        output_path=str(actual_output),
                        graph_name=graph_name or 'default',
                        resolution=(resolution, resolution)
                    )
                else:
                    # Try to find any output file
                    for f in output_dir.glob(f"*.{output_format}"):
                        logger.info(f"Found output file: {f}")
                        return RenderResult(
                            success=True,
                            output_path=str(f),
                            graph_name=graph_name or 'default',
                            resolution=(resolution, resolution)
                        )
                    
                    return RenderResult(
                        success=False,
                        output_path='',
                        graph_name=graph_name or '',
                        resolution=(resolution, resolution),
                        error=f"Output file not created. stdout: {result.stdout}"
                    )
            else:
                logger.error(f"sbsrender failed: {result.stderr}")
                return RenderResult(
                    success=False,
                    output_path='',
                    graph_name=graph_name or '',
                    resolution=(resolution, resolution),
                    error=f"sbsrender failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                output_path='',
                graph_name=graph_name or '',
                resolution=(resolution, resolution),
                error="Render timed out after 120 seconds"
            )
        except Exception as e:
            logger.exception(f"Render failed: {e}")
            return RenderResult(
                success=False,
                output_path='',
                graph_name=graph_name or '',
                resolution=(resolution, resolution),
                error=f"Render failed: {str(e)}"
            )
        finally:
            # Clean up temporary SBSAR file and directory
            if temp_sbsar and Path(temp_sbsar).exists():
                try:
                    Path(temp_sbsar).unlink()
                except:
                    pass
            if temp_sbsar_dir and Path(temp_sbsar_dir).exists():
                try:
                    import shutil
                    shutil.rmtree(temp_sbsar_dir, ignore_errors=True)
                except:
                    pass
    
    def render_all_outputs(
        self,
        filepath: str,
        output_dir: str,
        resolution: int = 256,
        output_format: str = 'png'
    ) -> List[RenderResult]:
        """
        Render all outputs from an SBS/SBSAR file.
        
        Args:
            filepath: Path to the SBS/SBSAR file.
            output_dir: Directory for output files.
            resolution: Output resolution.
            output_format: Output format.
            
        Returns:
            List of RenderResult for each output.
        """
        # Common output names to try
        output_names = [
            'basecolor', 'diffuse', 'albedo',
            'normal', 'height', 'roughness', 
            'metallic', 'ambientocclusion', 'ao'
        ]
        
        results = []
        for output_name in output_names:
            result = self.render(
                filepath=filepath,
                output_path=os.path.join(
                    output_dir, 
                    f"{Path(filepath).stem}_{output_name}.{output_format}"
                ),
                resolution=resolution,
                output_format=output_format,
                output_name=output_name
            )
            if result.success:
                results.append(result)
        
        return results
    
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
        
        # If SBS file, cook it first
        render_file = filepath
        if filepath.lower().endswith('.sbs'):
            success, sbsar_path, error = self.cook_sbs(filepath)
            if not success:
                return []
            render_file = sbsar_path
            
        cmd = [
            self.sbsrender_path,
            'info',
            '--input', render_file,
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse output to find available outputs
                outputs = []
                for line in result.stdout.split('\n'):
                    if 'OUTPUT' in line.upper():
                        # Extract output name from line
                        parts = line.split()
                        if len(parts) > 1:
                            outputs.append(parts[-1])
                return outputs
            return []
        except Exception:
            return []
