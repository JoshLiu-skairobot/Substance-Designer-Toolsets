"""
Parameters API Routes

REST API endpoints for parameter file management.
"""

from flask import Blueprint, request, jsonify, current_app
import json
from pathlib import Path

parameters_bp = Blueprint('parameters', __name__, url_prefix='/api/parameters')


# In-memory storage for parameter files
_parameter_files = {}


@parameters_bp.route('', methods=['GET'])
def list_parameters():
    """Get list of all parameter files."""
    files = list(_parameter_files.values())
    return jsonify(files)


@parameters_bp.route('/<path:filename>', methods=['GET'])
def get_parameter_file(filename):
    """Get a parameter file by filename."""
    if filename in _parameter_files:
        return jsonify(_parameter_files[filename])
    return jsonify({'error': 'Parameter file not found'}), 404


@parameters_bp.route('/extract', methods=['POST'])
def extract_parameters():
    """Extract parameters from an SBS/SBSAR file."""
    data = request.get_json()
    filepath = data.get('filepath')
    
    if not filepath:
        return jsonify({'error': 'No filepath provided'}), 400
    
    if not Path(filepath).exists():
        return jsonify({'error': f'File not found: {filepath}'}), 404
    
    try:
        from ...extractor import ParameterExtractor
        
        extractor = ParameterExtractor()
        result = extractor.extract(filepath)
        
        # Store in memory
        _parameter_files[result.filename] = result.to_dict()
        
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parameters_bp.route('/search', methods=['GET'])
def search_parameters():
    """Search parameter files."""
    query = request.args.get('query', '').lower()
    
    if not query:
        return jsonify(list(_parameter_files.values()))
    
    results = []
    for filename, data in _parameter_files.items():
        if query in filename.lower():
            results.append(data)
            continue
        
        # Search in graphs
        for graph in data.get('graphs', []):
            if query in graph.get('name', '').lower():
                results.append(data)
                break
    
    return jsonify(results)


@parameters_bp.route('/<path:filename>', methods=['DELETE'])
def delete_parameter_file(filename):
    """Delete a parameter file."""
    if filename in _parameter_files:
        del _parameter_files[filename]
        return jsonify({'success': True})
    return jsonify({'error': 'Parameter file not found'}), 404


@parameters_bp.route('/upload', methods=['POST'])
def upload_parameter_file():
    """Upload a JSON parameter file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        filename = data.get('filename', file.filename)
        _parameter_files[filename] = data
        
        return jsonify(data)
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON: {e}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
