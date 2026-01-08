"""
JSON Schema for Parameter Files

Defines the schema for extracted parameter JSON files,
providing validation and documentation.
"""

from typing import Dict, Any

# JSON Schema for parameter files
PARAMETER_FILE_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SAT Parameter File",
    "description": "Schema for extracted SBS/SBSAR parameters",
    "type": "object",
    "required": ["filename", "filepath", "fileType", "extractedAt", "graphs"],
    "properties": {
        "filename": {
            "type": "string",
            "description": "Name of the source file"
        },
        "filepath": {
            "type": "string",
            "description": "Full path to the source file"
        },
        "fileType": {
            "type": "string",
            "enum": ["sbs", "sbsar"],
            "description": "Type of Substance file"
        },
        "extractedAt": {
            "type": "string",
            "format": "date-time",
            "description": "ISO timestamp of extraction"
        },
        "graphs": {
            "type": "array",
            "items": {"$ref": "#/definitions/Graph"},
            "description": "List of graphs in the file"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "author": {"type": "string"},
                "description": {"type": "string"}
            },
            "description": "File metadata"
        }
    },
    "definitions": {
        "Graph": {
            "type": "object",
            "required": ["id", "name", "nodes"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "category": {"type": "string"},
                "nodes": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/Node"}
                }
            }
        },
        "Node": {
            "type": "object",
            "required": ["id", "name", "type", "parameters"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "category": {"type": "string"},
                "parameters": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/Parameter"}
                }
            }
        },
        "Parameter": {
            "type": "object",
            "required": ["id", "name", "label", "parameter"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "label": {"type": "string"},
                "description": {"type": "string"},
                "parameter": {"$ref": "#/definitions/ParameterValue"}
            }
        },
        "ParameterValue": {
            "type": "object",
            "required": ["type", "value"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["float", "float2", "float3", "float4",
                            "int", "int2", "int3", "int4",
                            "bool", "string", "enum", "image", "unknown"]
                },
                "value": {},
                "defaultValue": {},
                "min": {"type": "number"},
                "max": {"type": "number"},
                "step": {"type": "number"},
                "options": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}


class ParameterSchema:
    """
    Utility class for working with parameter file schemas.
    """
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get the JSON schema for parameter files."""
        return PARAMETER_FILE_SCHEMA
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> bool:
        """
        Validate data against the parameter file schema.
        
        Args:
            data: Dictionary to validate.
            
        Returns:
            True if valid, raises exception if invalid.
        """
        try:
            import jsonschema
            jsonschema.validate(data, PARAMETER_FILE_SCHEMA)
            return True
        except ImportError:
            # If jsonschema is not installed, do basic validation
            required = ["filename", "filepath", "fileType", "extractedAt", "graphs"]
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Schema validation failed: {e.message}")
    
    @staticmethod
    def generate_example() -> Dict[str, Any]:
        """Generate an example parameter file structure."""
        return {
            "filename": "example_material.sbs",
            "filepath": "/path/to/example_material.sbs",
            "fileType": "sbs",
            "extractedAt": "2024-01-01T12:00:00.000Z",
            "graphs": [
                {
                    "id": "graph_1",
                    "name": "Example Graph",
                    "description": "An example graph",
                    "category": "Material",
                    "nodes": [
                        {
                            "id": "node_1",
                            "name": "uniform_color",
                            "type": "Uniform Color",
                            "category": "Generator",
                            "parameters": [
                                {
                                    "id": "node_1_color",
                                    "name": "outputcolor",
                                    "label": "Output Color",
                                    "description": "The output color",
                                    "parameter": {
                                        "type": "float4",
                                        "value": [0.5, 0.5, 0.5, 1.0],
                                        "defaultValue": [0.5, 0.5, 0.5, 1.0]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ],
            "metadata": {
                "version": "1.0",
                "author": "Example Author",
                "description": "An example material"
            }
        }
