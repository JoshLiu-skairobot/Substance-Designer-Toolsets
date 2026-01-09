"""
Thumbnails API Routes

REST API endpoints for thumbnail management.
"""

from flask import Blueprint, request, jsonify, send_file, current_app
import json
from pathlib import Path
from datetime import datetime

thumbnails_bp = Blueprint('thumbnails', __name__, url_prefix='/api/thumbnails')


# In-memory storage for thumbnails
_thumbnails = {}


@thumbnails_bp.route('', methods=['GET'])
def list_thumbnails():
    """Get list of all thumbnails."""
    thumbnails = list(_thumbnails.values())
    return jsonify(thumbnails)


@thumbnails_bp.route('/<thumbnail_id>', methods=['GET'])
def get_thumbnail(thumbnail_id):
    """Get a thumbnail by ID."""
    if thumbnail_id in _thumbnails:
        return jsonify(_thumbnails[thumbnail_id])
    return jsonify({'error': 'Thumbnail not found'}), 404


@thumbnails_bp.route('/<thumbnail_id>/metadata', methods=['GET'])
def get_thumbnail_metadata(thumbnail_id):
    """Get thumbnail metadata."""
    if thumbnail_id in _thumbnails:
        return jsonify(_thumbnails[thumbnail_id].get('metadata', {}))
    return jsonify({'error': 'Thumbnail not found'}), 404


@thumbnails_bp.route('/generate', methods=['POST'])
def generate_thumbnail():
    """Generate a thumbnail from an SBS/SBSAR file."""
    data = request.get_json()
    filepath = data.get('filepath')
    resolution = data.get('resolution', 512)
    output_format = data.get('format', 'png')
    use_material_ball = data.get('useMaterialBall', True)
    
    if not filepath:
        return jsonify({'error': 'No filepath provided'}), 400
    
    if not Path(filepath).exists():
        return jsonify({'error': f'File not found: {filepath}'}), 404
    
    try:
        from ...thumbnail import ThumbnailRenderer, ThumbnailMetadata, MetadataWriter
        
        renderer = ThumbnailRenderer()
        result = renderer.render(
            filepath=filepath,
            resolution=resolution,
            output_format=output_format,
            use_material_ball=use_material_ball
        )
        
        if not result.success:
            return jsonify({'error': result.error}), 500
        
        # Create and embed metadata
        metadata = ThumbnailMetadata.create(
            source_file=filepath,
            graph_name=result.graph_name,
            resolution=result.resolution
        )
        
        if output_format == 'png':
            writer = MetadataWriter()
            writer.write(result.output_path, metadata)
        
        # Store thumbnail info
        import uuid
        thumbnail_id = str(uuid.uuid4())
        
        storage = current_app.config['storage']
        storage_path, url = storage.save_file(result.output_path)
        
        thumbnail_data = {
            'id': thumbnail_id,
            'filename': Path(result.output_path).name,
            'filepath': storage_path,
            'url': url,
            'metadata': metadata.to_dict(),
            'createdAt': datetime.utcnow().isoformat()
        }
        _thumbnails[thumbnail_id] = thumbnail_data
        
        return jsonify(thumbnail_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@thumbnails_bp.route('/batch', methods=['POST'])
def batch_generate():
    """Batch generate thumbnails."""
    data = request.get_json()
    directory = data.get('directory')
    resolution = data.get('resolution', 512)
    output_format = data.get('format', 'png')
    use_material_ball = data.get('useMaterialBall', True)
    
    if not directory:
        return jsonify({'error': 'No directory provided'}), 400
    
    if not Path(directory).exists():
        return jsonify({'error': f'Directory not found: {directory}'}), 404
    
    try:
        from ...thumbnail import BatchProcessor
        
        processor = BatchProcessor()
        
        # Create temp output directory
        import tempfile
        output_dir = tempfile.mkdtemp(prefix='sat_batch_')
        
        result = processor.process_directory(
            directory=directory,
            output_dir=output_dir,
            resolution=resolution,
            output_format=output_format,
            use_material_ball=use_material_ball
        )
        
        # Store thumbnails
        thumbnails = []
        storage = current_app.config['storage']
        
        for item in result.results:
            if item.get('success') and item.get('output'):
                import uuid
                thumbnail_id = str(uuid.uuid4())
                
                storage_path, url = storage.save_file(item['output'])
                
                thumbnail_data = {
                    'id': thumbnail_id,
                    'filename': Path(item['output']).name,
                    'filepath': storage_path,
                    'url': url,
                    'metadata': {
                        'sourceFile': item.get('file', ''),
                        'generatedAt': datetime.utcnow().isoformat()
                    },
                    'createdAt': datetime.utcnow().isoformat()
                }
                _thumbnails[thumbnail_id] = thumbnail_data
                thumbnails.append(thumbnail_data)
        
        return jsonify(thumbnails)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@thumbnails_bp.route('/<thumbnail_id>/metadata', methods=['POST'])
def update_metadata(thumbnail_id):
    """Update thumbnail metadata."""
    if thumbnail_id not in _thumbnails:
        return jsonify({'error': 'Thumbnail not found'}), 404
    
    data = request.get_json()
    
    thumbnail = _thumbnails[thumbnail_id]
    if 'metadata' not in thumbnail:
        thumbnail['metadata'] = {}
    
    thumbnail['metadata'].update(data)
    
    return jsonify(thumbnail)


@thumbnails_bp.route('/<thumbnail_id>', methods=['DELETE'])
def delete_thumbnail(thumbnail_id):
    """Delete a thumbnail."""
    if thumbnail_id not in _thumbnails:
        return jsonify({'error': 'Thumbnail not found'}), 404
    
    thumbnail = _thumbnails[thumbnail_id]
    
    # Delete file
    storage = current_app.config['storage']
    storage.delete_file(thumbnail.get('filepath', ''))
    
    del _thumbnails[thumbnail_id]
    
    return jsonify({'success': True})
