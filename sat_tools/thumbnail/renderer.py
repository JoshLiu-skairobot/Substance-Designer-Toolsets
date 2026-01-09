"""
Thumbnail Renderer Module

Provides functionality to render thumbnails from SBS/SBSAR files
using sbsrender command-line tool.
"""

import os
import subprocess
import tempfile
import logging
import math
import shutil
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
        
        # Path to internal material ball renderer
        self.material_ball_sbsar = None
        if self.sat_path:
            mb_path = os.path.join(self.sat_path, 'resources', 'internal', 'material_thumbnail_render.sbsar')
            if os.path.exists(mb_path):
                self.material_ball_sbsar = mb_path
                logger.info(f"Found material ball renderer: {self.material_ball_sbsar}")
            else:
                logger.warning(f"Material ball renderer not found at: {mb_path}")
        
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
                timeout=300
            )
            
            if result.returncode == 0:
                if Path(sbsar_path).exists():
                    logger.info(f"Successfully cooked to: {sbsar_path}")
                    return True, sbsar_path, None
                else:
                    return False, '', f"SBSAR file not created: {sbsar_path}"
            else:
                logger.error(f"sbscooker failed: {result.stderr}")
                return False, '', f"sbscooker failed: {result.stderr}"
                
        except Exception as e:
            return False, '', f"Cooking failed: {str(e)}"

    def _render_material_ball(
        self,
        sbsar_path: str,
        output_path: Optional[str] = None,
        resolution: int = 512,
        output_format: str = 'png',
        graph_name: Optional[str] = None
    ) -> RenderResult:
        """
        Renders a material ball using the internal material_thumbnail_render.sbsar.
        """
        if not self.material_ball_sbsar:
            return RenderResult(
                success=False, 
                output_path='', 
                graph_name='', 
                resolution=(resolution, resolution), 
                error="Material ball renderer not found"
            )

        temp_dir = tempfile.mkdtemp(prefix='sat_mb_maps_')
        try:
            # 1. Get graph info to find available outputs
            graphs = self.get_graph_info(sbsar_path)
            if not graphs:
                return RenderResult(
                    success=False, 
                    output_path='', 
                    graph_name='', 
                    resolution=(resolution, resolution), 
                    error="Could not get graph info"
                )
            
            target_graph = None
            if graph_name:
                for g in graphs:
                    if g.name == graph_name:
                        target_graph = g
                        break
            
            if not target_graph:
                target_graph = graphs[0]
                graph_name = target_graph.name

            # 2. Render necessary maps
            maps_to_render = {
                'basecolor': ['basecolor', 'baseColor', 'diffuse', 'albedo'],
                'normal': ['normal', 'Normal'],
                'roughness': ['roughness', 'Roughness'],
                'metallic': ['metallic', 'Metallic', 'metalness'],
                'height': ['height', 'Height', 'displacement'],
                'emissive': ['emissive', 'Emissive']
            }

            rendered_maps = {}
            # Clamp resolution for maps and final render
            resolution = max(256, min(2048, resolution))
            map_res_log2 = int(math.log2(resolution))
            
            available_outputs = {out.name.lower(): out.name for out in target_graph.outputs}
            available_usages = {out.usage.lower(): out.name for out in target_graph.outputs}

            for map_type, possible_names in maps_to_render.items():
                target_output = None
                for name in possible_names:
                    if name.lower() in available_outputs:
                        target_output = available_outputs[name.lower()]
                        break
                    if name.lower() in available_usages:
                        target_output = available_usages[name.lower()]
                        break
                
                if target_output:
                    map_file_name = f"{map_type}.png"
                    cmd = [
                        self.sbsrender_path, 'render',
                        '--input', sbsar_path,
                        '--input-graph', graph_name,
                        '--input-graph-output', target_output,
                        '--output-path', temp_dir,
                        '--output-name', map_type,
                        '--output-format', 'png',
                        '--set-value', f'$outputsize@{map_res_log2},{map_res_log2}'
                    ]
                    subprocess.run(cmd, capture_output=True, check=False)
                    map_file_path = os.path.join(temp_dir, map_file_name)
                    if os.path.exists(map_file_path):
                        rendered_maps[map_type] = map_file_path

            # 3. Use material_thumbnail_render.sbsar to render final image
            if output_path is None:
                final_output_dir = tempfile.mkdtemp(prefix='sat_mb_final_')
                output_path = os.path.join(final_output_dir, f"thumbnail.{output_format}")
            else:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.sbsrender_path, 'render',
                '--input', self.material_ball_sbsar,
                '--output-path', str(Path(output_path).parent),
                '--output-name', Path(output_path).stem,
                '--output-format', output_format,
                '--set-value', f'$outputsize@{map_res_log2},{map_res_log2}'
            ]

            for map_type, map_file in rendered_maps.items():
                cmd.extend(['--set-entry', f'{map_type}@{map_file}'])

            logger.info(f"Rendering material ball: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                actual_output = Path(output_path).parent / f"{Path(output_path).stem}.{output_format}"
                if actual_output.exists():
                    return RenderResult(
                        success=True,
                        output_path=str(actual_output),
                        graph_name=graph_name,
                        resolution=(resolution, resolution)
                    )
            
            return RenderResult(
                success=False,
                output_path='',
                graph_name=graph_name,
                resolution=(resolution, resolution),
                error=f"Material ball render failed: {result.stderr}"
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def render(
        self,
        filepath: str,
        output_path: Optional[str] = None,
        resolution: int = 512,
        output_format: str = 'png',
        graph_name: Optional[str] = None,
        output_name: str = 'basecolor',
        use_material_ball: bool = True
    ) -> RenderResult:
        """
        Render a thumbnail from an SBS/SBSAR file.
        """
        if self.sbsrender_path is None:
            return RenderResult(
                success=False,
                output_path='',
                graph_name=graph_name or '',
                resolution=(resolution, resolution),
                error="sbsrender not found."
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
        
        render_file = str(filepath)
        temp_sbsar = None
        temp_sbsar_dir = None
        
        if filepath.suffix.lower() == '.sbs':
            success, sbsar_path, error = self.cook_sbs(str(filepath))
            if not success:
                return RenderResult(
                    success=False,
                    output_path='',
                    graph_name=graph_name or '',
                    resolution=(resolution, resolution),
                    error=f"Failed to cook SBS: {error}"
                )
            render_file = sbsar_path
            temp_sbsar = sbsar_path
            temp_sbsar_dir = str(Path(sbsar_path).parent)
        
        try:
            if use_material_ball and self.material_ball_sbsar:
                return self._render_material_ball(
                    render_file, 
                    output_path, 
                    resolution, 
                    output_format, 
                    graph_name
                )
            
            # Flat rendering fallback
            if graph_name is None:
                graphs = self.get_graph_info(render_file)
                if graphs:
                    detected_graph, detected_output = self.find_best_graph(graphs)
                    if detected_graph:
                        graph_name = detected_graph
                        output_name = detected_output or output_name
            
            if output_path is None:
                output_dir = tempfile.mkdtemp(prefix='sat_thumb_')
                output_path = os.path.join(output_dir, f"{filepath.stem}_preview.{output_format}")
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            log2_res = max(5, min(13, int(math.log2(resolution))))
            
            cmd = [
                self.sbsrender_path, 'render',
                '--input', render_file,
                '--output-path', str(Path(output_path).parent),
                '--output-name', Path(output_path).stem,
                '--output-format', output_format,
                '--set-value', f'$outputsize@{log2_res},{log2_res}',
            ]
            if graph_name:
                cmd.extend(['--input-graph', graph_name])
            cmd.extend(['--input-graph-output', output_name])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                actual_output = Path(output_path).parent / f"{Path(output_path).stem}.{output_format}"
                if actual_output.exists():
                    return RenderResult(
                        success=True,
                        output_path=str(actual_output),
                        graph_name=graph_name or 'default',
                        resolution=(resolution, resolution)
                    )
            
            return RenderResult(
                success=False, output_path='', graph_name=graph_name or '', resolution=(resolution, resolution),
                error=f"Flat render failed: {result.stderr}"
            )
        finally:
            if temp_sbsar and Path(temp_sbsar).exists():
                try: Path(temp_sbsar).unlink()
                except: pass
            if temp_sbsar_dir and Path(temp_sbsar_dir).exists():
                shutil.rmtree(temp_sbsar_dir, ignore_errors=True)

    def render_all_outputs(
        self,
        filepath: str,
        output_dir: str,
        resolution: int = 512,
        output_format: str = 'png'
    ) -> List[RenderResult]:
        """
        Render all outputs from an SBS/SBSAR file.
        """
        output_names = [
            'basecolor', 'diffuse', 'albedo',
            'normal', 'height', 'roughness', 
            'metallic', 'ambientocclusion', 'ao'
        ]
        
        results = []
        for output_name in output_names:
            result = self.render(
                filepath=filepath,
                output_path=os.path.join(output_dir, f"{Path(filepath).stem}_{output_name}.{output_format}"),
                resolution=resolution,
                output_format=output_format,
                output_name=output_name,
                use_material_ball=False # When rendering all maps, we don't want the ball
            )
            if result.success:
                results.append(result)
        
        return results

    def get_available_outputs(self, filepath: str) -> List[str]:
        """
        Get list of available outputs from an SBS/SBSAR file.
        """
        if self.sbsrender_path is None:
            return []
        
        render_file = filepath
        temp_sbsar = None
        if filepath.lower().endswith('.sbs'):
            success, sbsar_path, error = self.cook_sbs(filepath)
            if not success:
                return []
            render_file = sbsar_path
            temp_sbsar = sbsar_path
            
        cmd = [self.sbsrender_path, 'info', '--input', render_file]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                outputs = []
                for line in result.stdout.split('\n'):
                    if 'OUTPUT' in line.upper():
                        parts = line.split()
                        if len(parts) > 1:
                            outputs.append(parts[-1])
                return outputs
            return []
        except:
            return []
        finally:
            if temp_sbsar and Path(temp_sbsar).exists():
                try: Path(temp_sbsar).unlink()
                except: pass
