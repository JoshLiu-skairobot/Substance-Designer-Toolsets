"""
Parameter Extractor Module

Extracts parameters from SBS/SBSAR graph nodes and converts them
to a structured format.
"""

import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import re
import tempfile

# Setup logging
logger = logging.getLogger(__name__)


class ParameterType(str, Enum):
    """Supported parameter types."""
    FLOAT = "float"
    FLOAT2 = "float2"
    FLOAT3 = "float3"
    FLOAT4 = "float4"
    INT = "int"
    INT2 = "int2"
    INT3 = "int3"
    INT4 = "int4"
    BOOL = "bool"
    STRING = "string"
    ENUM = "enum"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass
class ParameterValue:
    """Represents a parameter value with type info."""
    type: ParameterType
    value: Any
    default_value: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[str]] = None  # For enum types
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = {
            'type': self.type.value,
            'value': self.value,
        }
        if self.default_value is not None:
            result['defaultValue'] = self.default_value
        if self.min_value is not None:
            result['min'] = self.min_value
        if self.max_value is not None:
            result['max'] = self.max_value
        if self.step is not None:
            result['step'] = self.step
        if self.options is not None:
            result['options'] = self.options
        return result


class ParameterExtractor:
    """
    Extracts parameters from SBS/SBSAR files.
    
    Uses sbsrender info command to get accurate parameter information.
    """
    
    def __init__(self, sat_install_path: Optional[str] = None):
        """
        Initialize the extractor.
        
        Args:
            sat_install_path: Path to SAT installation.
        """
        self.sat_path = sat_install_path or self._detect_sat_path()
        self.sbsrender_path = self._find_tool('sbsrender')
        self.sbscooker_path = self._find_tool('sbscooker')
        
        logger.info(f"SAT path: {self.sat_path}")
        logger.info(f"sbsrender path: {self.sbsrender_path}")
        logger.info(f"sbscooker path: {self.sbscooker_path}")
    
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
        
        exe_name = f"{tool_name}.exe" if os.name == 'nt' else tool_name
        candidates = [
            os.path.join(self.sat_path, exe_name),
            os.path.join(self.sat_path, 'bin', exe_name),
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        return None
    
    def _cook_sbs_to_sbsar(self, sbs_path: str) -> tuple:
        """
        Cook an SBS file to SBSAR.
        
        Returns:
            Tuple of (success, sbsar_path, error)
        """
        if self.sbscooker_path is None:
            return False, '', "sbscooker not found"
        
        sbs_file = Path(sbs_path)
        if not sbs_file.exists():
            return False, '', f"SBS file not found: {sbs_path}"
        
        output_dir = tempfile.mkdtemp(prefix='sat_extract_')
        sbsar_path = os.path.join(output_dir, f"{sbs_file.stem}.sbsar")
        
        cmd = [
            self.sbscooker_path,
            '--inputs', str(sbs_file),
            '--output-path', output_dir,
            '--output-name', sbs_file.stem,
        ]
        
        logger.info(f"Cooking SBS to SBSAR: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and Path(sbsar_path).exists():
                logger.info(f"Successfully cooked to: {sbsar_path}")
                return True, sbsar_path, None
            else:
                error = result.stderr or "Unknown error"
                logger.error(f"Cook failed: {error}")
                return False, '', f"sbscooker failed: {error}"
        except Exception as e:
            logger.error(f"Cook exception: {e}")
            return False, '', str(e)
    
    def _run_sbsrender_info(self, filepath: str) -> Dict[str, Any]:
        """
        Run sbsrender info to get package information.
        
        Returns:
            Dictionary with parsed info output.
        """
        if self.sbsrender_path is None:
            raise RuntimeError("sbsrender not found")
        
        cmd = [
            self.sbsrender_path,
            'info',
            '--input', filepath,
        ]
        
        logger.info(f"Running sbsrender info: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        logger.debug(f"sbsrender info output:\n{result.stdout}")
        
        if result.returncode != 0:
            logger.error(f"sbsrender info failed: {result.stderr}")
            raise RuntimeError(f"sbsrender info failed: {result.stderr}")
        
        return self._parse_info_output(result.stdout)
    
    def _parse_info_output(self, output: str) -> Dict[str, Any]:
        """
        Parse the sbsrender info output.
        
        Returns:
            Structured dictionary with graphs and parameters.
        """
        result = {
            'graphs': [],
            'raw_output': output
        }
        
        lines = output.split('\n')
        current_graph = None
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Parse graph declarations
            if line.startswith('GRAPH-URL'):
                # Save previous graph
                if current_graph:
                    result['graphs'].append(current_graph)
                
                # Extract graph URL
                match = re.search(r'pkg:///([^\s]+)', line)
                graph_name = match.group(1) if match else 'Unknown'
                
                current_graph = {
                    'id': graph_name,
                    'name': graph_name,
                    'url': line.split()[-1] if line.split() else '',
                    'inputs': [],
                    'outputs': [],
                    'parameters': []
                }
                current_section = None
                
            elif line.startswith('INPUT'):
                if current_graph:
                    # Parse input: INPUT identifier (type)
                    parts = line.split()
                    if len(parts) >= 2:
                        identifier = parts[1]
                        param_type = 'unknown'
                        
                        # Try to extract type from parentheses
                        type_match = re.search(r'\(([^)]+)\)', line)
                        if type_match:
                            param_type = type_match.group(1)
                        
                        # Parse additional info like default value
                        default_value = None
                        value_match = re.search(r'DEFAULT\[([^\]]+)\]', line)
                        if value_match:
                            try:
                                default_value = eval(value_match.group(1))
                            except:
                                default_value = value_match.group(1)
                        
                        current_graph['inputs'].append({
                            'id': identifier,
                            'name': identifier,
                            'label': identifier.replace('_', ' ').title(),
                            'type': self._normalize_type(param_type),
                            'value': default_value,
                            'defaultValue': default_value,
                        })
                        
            elif line.startswith('OUTPUT'):
                if current_graph:
                    # Parse output: OUTPUT identifier (usage)
                    parts = line.split()
                    if len(parts) >= 2:
                        identifier = parts[1]
                        usage = 'unknown'
                        
                        usage_match = re.search(r'\(([^)]+)\)', line)
                        if usage_match:
                            usage = usage_match.group(1)
                        
                        current_graph['outputs'].append({
                            'id': identifier,
                            'name': identifier,
                            'usage': usage,
                        })
        
        # Don't forget last graph
        if current_graph:
            result['graphs'].append(current_graph)
        
        logger.info(f"Parsed {len(result['graphs'])} graph(s)")
        
        return result
    
    def _normalize_type(self, raw_type: str) -> str:
        """Normalize parameter type string."""
        raw_type = raw_type.lower().strip()
        
        type_map = {
            'float1': 'float',
            'float2': 'float2',
            'float3': 'float3',
            'float4': 'float4',
            'integer1': 'int',
            'integer2': 'int2',
            'integer3': 'int3',
            'integer4': 'int4',
            'int1': 'int',
            'boolean': 'bool',
            'string': 'string',
            'entry': 'enum',
            'image': 'image',
        }
        
        return type_map.get(raw_type, raw_type)
    
    def extract(self, filepath: str) -> Dict[str, Any]:
        """
        Extract all parameters from an SBS/SBSAR file.
        
        Args:
            filepath: Path to the file.
            
        Returns:
            Dictionary with extraction results.
        """
        from datetime import datetime
        
        logger.info(f"Extracting parameters from: {filepath}")
        
        path = Path(filepath)
        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return {
                'success': False,
                'error': f'File not found: {filepath}'
            }
        
        try:
            # If SBS file, cook it first
            render_file = str(path)
            temp_sbsar = None
            
            if path.suffix.lower() == '.sbs':
                logger.info("Cooking SBS to SBSAR for parameter extraction")
                success, sbsar_path, error = self._cook_sbs_to_sbsar(str(path))
                if not success:
                    return {
                        'success': False,
                        'error': f'Failed to cook SBS: {error}'
                    }
                render_file = sbsar_path
                temp_sbsar = sbsar_path
            
            # Run sbsrender info
            info = self._run_sbsrender_info(render_file)
            
            # Build result structure
            graphs = []
            for graph_info in info.get('graphs', []):
                nodes = []
                
                # Convert inputs to node parameters
                for input_param in graph_info.get('inputs', []):
                    nodes.append({
                        'id': f"param_{input_param['id']}",
                        'name': input_param['name'],
                        'type': 'Input Parameter',
                        'category': 'Input',
                        'parameters': [{
                            'id': input_param['id'],
                            'name': input_param['name'],
                            'label': input_param.get('label', input_param['name']),
                            'parameter': {
                                'type': input_param.get('type', 'unknown'),
                                'value': input_param.get('value'),
                                'defaultValue': input_param.get('defaultValue'),
                            }
                        }]
                    })
                
                # Add outputs as info
                for output in graph_info.get('outputs', []):
                    nodes.append({
                        'id': f"output_{output['id']}",
                        'name': output['name'],
                        'type': 'Output',
                        'category': 'Output',
                        'parameters': [{
                            'id': output['id'],
                            'name': output['name'],
                            'label': output['name'],
                            'parameter': {
                                'type': 'output',
                                'value': output.get('usage', ''),
                                'defaultValue': None,
                            }
                        }]
                    })
                
                graphs.append({
                    'id': graph_info['id'],
                    'name': graph_info['name'],
                    'description': '',
                    'category': 'Material',
                    'nodes': nodes,
                })
            
            result = {
                'success': True,
                'data': {
                    'filename': path.name,
                    'filepath': str(path.absolute()),
                    'fileType': path.suffix[1:].lower(),
                    'extractedAt': datetime.now().isoformat(),
                    'graphs': graphs,
                    'metadata': {
                        'version': '1.0',
                        'author': '',
                        'description': f'Extracted from {path.name}',
                    }
                }
            }
            
            logger.info(f"Successfully extracted {len(graphs)} graph(s)")
            
            # Cleanup temp file
            if temp_sbsar and Path(temp_sbsar).exists():
                try:
                    Path(temp_sbsar).unlink()
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_to_json(self, filepath: str, output_path: Optional[str] = None) -> str:
        """
        Extract parameters and save to JSON file.
        
        Args:
            filepath: Path to the SBS/SBSAR file.
            output_path: Path for the output JSON.
            
        Returns:
            Path to the saved JSON file.
        """
        result = self.extract(filepath)
        
        if not result.get('success'):
            raise RuntimeError(result.get('error', 'Unknown error'))
        
        if output_path is None:
            output_path = str(Path(filepath).with_suffix('.json'))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result['data'], f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved parameters to: {output_path}")
        return output_path
