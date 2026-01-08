"""
SBS/SBSAR Parser Module

Provides functionality to load and parse Substance Designer files
using the pysbs API.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class GraphInfo:
    """Information about a graph in an SBS/SBSAR file."""
    identifier: str
    label: str
    description: str
    category: str
    pkgurl: str


@dataclass
class NodeInfo:
    """Information about a node in a graph."""
    identifier: str
    definition: str
    gui_name: str
    position: tuple
    

class SBSParser:
    """
    Parser for SBS and SBSAR files.
    
    Uses pysbs API to load and parse Substance Designer files,
    extracting graph and node information.
    """
    
    def __init__(self, sat_install_path: Optional[str] = None):
        """
        Initialize the parser.
        
        Args:
            sat_install_path: Path to Substance Automation Toolkit installation.
                            If None, will try to detect automatically.
        """
        self.sat_path = sat_install_path or self._detect_sat_path()
        self._pysbs = None
        self._context = None
        self._loaded_doc = None
        
    def _detect_sat_path(self) -> Optional[str]:
        """Detect SAT installation path."""
        # Common installation paths
        possible_paths = [
            # Windows
            r"C:\Program Files\Adobe\Adobe Substance 3D Automation Toolkit",
            r"C:\Program Files\Allegorithmic\Substance Automation Toolkit",
            # Linux
            "/opt/Adobe/Adobe_Substance_3D_Automation_Toolkit",
            "/opt/Allegorithmic/Substance_Automation_Toolkit",
            # Relative to project
            str(Path(__file__).parent.parent.parent / 
                "Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _init_pysbs(self):
        """Initialize pysbs module if not already done."""
        if self._pysbs is not None:
            return
            
        try:
            import pysbs
            from pysbs import context
            
            self._pysbs = pysbs
            self._context = context.Context()
        except ImportError as e:
            raise ImportError(
                f"Failed to import pysbs. Make sure the Substance Automation Toolkit "
                f"is installed and pysbs wheel is installed. Error: {e}"
            )
    
    def load(self, filepath: str) -> bool:
        """
        Load an SBS or SBSAR file.
        
        Args:
            filepath: Path to the SBS/SBSAR file.
            
        Returns:
            True if loaded successfully, False otherwise.
        """
        self._init_pysbs()
        
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        ext = filepath.suffix.lower()
        if ext not in ['.sbs', '.sbsar']:
            raise ValueError(f"Unsupported file type: {ext}. Must be .sbs or .sbsar")
        
        try:
            if ext == '.sbs':
                self._loaded_doc = self._pysbs.substance.SBSDocument(
                    self._context, str(filepath)
                )
                self._loaded_doc.parseDoc()
            else:
                # SBSAR files are compiled packages
                self._loaded_doc = self._pysbs.sbsarchive.SBSArchive(
                    self._context, str(filepath)
                )
                self._loaded_doc.parseDoc()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to load file: {e}")
    
    def get_graphs(self) -> List[GraphInfo]:
        """
        Get all graphs from the loaded document.
        
        Returns:
            List of GraphInfo objects.
        """
        if self._loaded_doc is None:
            raise RuntimeError("No document loaded. Call load() first.")
            
        graphs = []
        
        try:
            # Get SBS graphs
            if hasattr(self._loaded_doc, 'getSBSGraphList'):
                for graph in self._loaded_doc.getSBSGraphList():
                    graphs.append(GraphInfo(
                        identifier=graph.mIdentifier or '',
                        label=graph.getGraphOutputNameLabel() if hasattr(graph, 'getGraphOutputNameLabel') else graph.mIdentifier or '',
                        description=graph.mDescription or '',
                        category=graph.mCategory or 'Uncategorized',
                        pkgurl=graph.getPkgUrl() if hasattr(graph, 'getPkgUrl') else ''
                    ))
            # Get SBSAR graphs
            elif hasattr(self._loaded_doc, 'getSBSARGraphList'):
                for graph in self._loaded_doc.getSBSARGraphList():
                    graphs.append(GraphInfo(
                        identifier=graph.mIdentifier or '',
                        label=graph.mLabel or graph.mIdentifier or '',
                        description=graph.mDescription or '',
                        category=graph.mCategory or 'Uncategorized',
                        pkgurl=graph.mPkgUrl or ''
                    ))
        except Exception as e:
            raise RuntimeError(f"Failed to get graphs: {e}")
            
        return graphs
    
    def get_graph_nodes(self, graph_identifier: str) -> List[NodeInfo]:
        """
        Get all nodes from a specific graph.
        
        Args:
            graph_identifier: The identifier of the graph.
            
        Returns:
            List of NodeInfo objects.
        """
        if self._loaded_doc is None:
            raise RuntimeError("No document loaded. Call load() first.")
            
        nodes = []
        
        try:
            graph = None
            if hasattr(self._loaded_doc, 'getSBSGraph'):
                graph = self._loaded_doc.getSBSGraph(graph_identifier)
            
            if graph is None:
                raise ValueError(f"Graph not found: {graph_identifier}")
                
            if hasattr(graph, 'getAllNodes'):
                for node in graph.getAllNodes():
                    nodes.append(NodeInfo(
                        identifier=node.mUID or '',
                        definition=node.getDefinition() if hasattr(node, 'getDefinition') else '',
                        gui_name=node.getGuiName() if hasattr(node, 'getGuiName') else '',
                        position=node.getPosition() if hasattr(node, 'getPosition') else (0, 0)
                    ))
        except Exception as e:
            raise RuntimeError(f"Failed to get nodes: {e}")
            
        return nodes
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Get metadata about the loaded file.
        
        Returns:
            Dictionary containing file metadata.
        """
        if self._loaded_doc is None:
            raise RuntimeError("No document loaded. Call load() first.")
            
        info = {
            'format_version': '',
            'author': '',
            'description': '',
            'keywords': [],
        }
        
        try:
            if hasattr(self._loaded_doc, 'getFormatVersion'):
                info['format_version'] = self._loaded_doc.getFormatVersion()
            if hasattr(self._loaded_doc, 'mAuthor'):
                info['author'] = self._loaded_doc.mAuthor or ''
            if hasattr(self._loaded_doc, 'mDescription'):
                info['description'] = self._loaded_doc.mDescription or ''
            if hasattr(self._loaded_doc, 'mKeywords'):
                info['keywords'] = self._loaded_doc.mKeywords or []
        except Exception:
            pass
            
        return info
    
    def close(self):
        """Close the loaded document and free resources."""
        self._loaded_doc = None
