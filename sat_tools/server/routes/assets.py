# -*- coding: utf-8 -*-
"""
Assets API Routes

REST API endpoints for asset management.
"""

import logging
import re
from flask import Blueprint, request, jsonify, current_app
import json
from pathlib import Path
import sys

# Setup logging
logger = logging.getLogger(__name__)


def _parse_sbscooker_error(error_msg: str) -> str:
    """Parse sbscooker error message and return a user-friendly message."""
    if not error_msg:
        return "Unknown error"
    
    # Check for missing dependency package
    match = re.search(r'package ([^\s]+) could not be found', error_msg)
    if match:
        missing_pkg = match.group(1)
        # Extract just the filename
        missing_file = Path(missing_pkg).name
        return (
            f"Missing SBS dependency: {missing_file}\n\n"
            f"This SBS file references an external file '{missing_file}' that does not exist on the server.\n\n"
            f"Solutions:\n"
            f"1. Upload all dependency SBS files first\n"
            f"2. Use compiled SBSAR format (no external dependencies needed)"
        )
    
    # Check for other common errors
    if "built-in packages location is not found" in error_msg:
        return (
            "SAT configuration issue: Built-in packages location not found.\n"
            "Please check if SAT installation path is correctly configured."
        )
    
    if "Cannot open the package" in error_msg:
        return "Cannot open SBS package. The file may be corrupted or in an invalid format."
    
    # Return original message if no pattern matched
    return error_msg


assets_bp = Blueprint('assets', __name__, url_prefix='/api/assets')


@assets_bp.route('', methods=['GET'])
def list_assets():
    """Get list of assets with pagination."""
    logger.info("Fetching asset list")
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    search = request.args.get('query', '')
    tags = request.args.getlist('tags')
    
    db = current_app.config['database']
    assets, total = db.get_assets(
        page=page,
        page_size=page_size,
        search=search if search else None,
        tags=tags if tags else None
    )
    
    # Get textures for each asset
    items = []
    for asset in assets:
        asset_dict = asset.to_dict()
        textures = db.get_textures_for_asset(asset.id)
        asset_dict['textures'] = [t.to_dict() for t in textures]
        items.append(asset_dict)
    
    logger.info(f"Returning {len(items)} assets (total: {total})")
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'pageSize': page_size,
        'totalPages': (total + page_size - 1) // page_size
    })


@assets_bp.route('/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """Get a single asset by ID."""
    logger.info(f"Getting asset: {asset_id}")
    db = current_app.config['database']
    asset = db.get_asset(asset_id)
    
    if not asset:
        logger.warning(f"Asset not found: {asset_id}")
        return jsonify({'error': 'Asset not found'}), 404
    
    asset_dict = asset.to_dict()
    textures = db.get_textures_for_asset(asset.id)
    asset_dict['textures'] = [t.to_dict() for t in textures]
    
    return jsonify(asset_dict)


@assets_bp.route('/upload', methods=['POST'])
def upload_asset():
    """
    Upload an SBS/SBSAR source file.
    
    This is the main entry point for adding new Substance files to the repository.
    The file is stored and an asset record is created. Thumbnails and texture
    baking can be done later.
    """
    logger.info("Uploading new asset")
    
    if 'file' not in request.files:
        logger.error("No file provided in upload request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("Empty filename in upload request")
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    filename = file.filename
    if not filename.lower().endswith(('.sbs', '.sbsar')):
        logger.error(f"Invalid file type: {filename}")
        return jsonify({'error': 'Only SBS and SBSAR files are allowed'}), 400
    
    file_type = 'sbs' if filename.lower().endswith('.sbs') else 'sbsar'
    
    name = request.form.get('name', Path(filename).stem)
    description = request.form.get('description', f'Substance {file_type.upper()} file')
    tags = json.loads(request.form.get('tags', '[]'))
    
    db = current_app.config['database']
    storage = current_app.config['storage']
    
    from ..models import Asset
    
    # Create asset
    asset = Asset.create(
        name=name,
        source_file=filename,
        file_type=file_type,
        description=description,
        tags=tags + [file_type, 'uploaded']
    )
    
    # Save source file to storage
    file_data = file.read()
    storage_path, source_url = storage.save_uploaded_file(
        file_data,
        filename,
        asset.id
    )
    
    asset.storage_path = storage_path
    asset.source_file_url = source_url
    
    # Generate placeholder thumbnail URL
    asset.thumbnail_url = f"https://via.placeholder.com/128/6366f1/ffffff?text={file_type.upper()}"
    
    # Save to database
    db.save_asset(asset)
    
    logger.info(f"Asset uploaded successfully: {asset.id} ({filename})")
    logger.info(f"Storage path: {storage_path}")
    
    # Auto-process: Extract parameters and generate thumbnail
    auto_process_results = _auto_process_asset(asset, db, storage)
    
    # Reload asset to get updated data
    asset = db.get_asset(asset.id)
    
    return jsonify({
        'id': asset.id,
        'assetId': asset.id,
        'name': asset.name,
        'sourceFile': asset.source_file,
        'sourceFileUrl': asset.source_file_url,
        'fileType': file_type,
        'storagePath': storage_path,
        'thumbnailUrl': asset.thumbnail_url,
        'hasParameters': asset.has_parameters,
        'hasThumbnail': asset.has_thumbnail,
        'hasBakedTextures': asset.has_baked_textures,
        'autoProcess': auto_process_results
    }), 201


def _auto_process_asset(asset, db, storage):
    """Auto-process asset: extract parameters and generate thumbnail."""
    from datetime import datetime
    results = {
        'parameters': {'success': False, 'error': None},
        'thumbnail': {'success': False, 'error': None}
    }
    
    # 1. Extract parameters
    try:
        from extractor.extractor import ParameterExtractor
        logger.info(f"Auto-extracting parameters for asset: {asset.id}")
        
        extractor = ParameterExtractor()
        param_result = extractor.extract(asset.storage_path)
        
        if param_result.get('success', False):
            asset.has_parameters = True
            asset.metadata = asset.metadata or {}
            asset.metadata['parameters'] = param_result.get('data', {})
            results['parameters']['success'] = True
            logger.info(f"Parameters extracted successfully for asset: {asset.id}")
        else:
            raw_error = param_result.get('error', 'Unknown error')
            results['parameters']['error'] = _parse_sbscooker_error(raw_error)
            logger.warning(f"Parameter extraction failed: {raw_error}")
    except Exception as e:
        results['parameters']['error'] = str(e)
        logger.warning(f"Parameter extraction failed: {e}")
    
    # 2. Generate thumbnail
    try:
        from thumbnail.renderer import ThumbnailRenderer
        logger.info(f"Auto-generating thumbnail for asset: {asset.id}")
        
        renderer = ThumbnailRenderer()
        render_result = renderer.render(
            filepath=asset.storage_path,
            resolution=256,
            output_format='png'
        )
        
        if render_result.success:
            # Save thumbnail to storage
            thumb_storage_path, thumb_url = storage.save_file(
                render_result.output_path,
                f"{asset.id}_thumbnail.png",
                asset.id
            )
            
            asset.thumbnail_url = thumb_url
            asset.has_thumbnail = True
            results['thumbnail']['success'] = True
            results['thumbnail']['url'] = thumb_url
            logger.info(f"Thumbnail generated successfully for asset: {asset.id}")
        else:
            results['thumbnail']['error'] = _parse_sbscooker_error(render_result.error)
            logger.warning(f"Thumbnail generation failed: {render_result.error}")
    except Exception as e:
        results['thumbnail']['error'] = str(e)
        logger.warning(f"Thumbnail generation failed: {e}")
    
    # Save updated asset
    asset.updated_at = datetime.utcnow()
    db.save_asset(asset)
    
    return results


@assets_bp.route('/upload-batch', methods=['POST'])
def upload_batch():
    """Upload multiple SBS/SBSAR files."""
    logger.info("Batch uploading assets")
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    db = current_app.config['database']
    storage = current_app.config['storage']
    
    from ..models import Asset
    
    results = []
    for file in files:
        if file.filename == '':
            continue
        
        filename = file.filename
        if not filename.lower().endswith(('.sbs', '.sbsar')):
            results.append({
                'filename': filename,
                'error': 'Only SBS and SBSAR files are allowed'
            })
            continue
        
        file_type = 'sbs' if filename.lower().endswith('.sbs') else 'sbsar'
        
        # Create asset
        asset = Asset.create(
            name=Path(filename).stem,
            source_file=filename,
            file_type=file_type,
            description=f'Substance {file_type.upper()} file',
            tags=[file_type, 'uploaded', 'batch']
        )
        
        # Save source file
        file_data = file.read()
        storage_path, source_url = storage.save_uploaded_file(
            file_data,
            filename,
            asset.id
        )
        
        asset.storage_path = storage_path
        asset.source_file_url = source_url
        asset.thumbnail_url = f"https://via.placeholder.com/128/6366f1/ffffff?text={file_type.upper()}"
        
        db.save_asset(asset)
        
        logger.info(f"Batch upload: {asset.id} ({filename})")
        
        results.append({
            'id': asset.id,
            'filename': filename,
            'sourceFileUrl': source_url,
            'success': True
        })
    
    return jsonify({
        'uploaded': len([r for r in results if r.get('success')]),
        'failed': len([r for r in results if r.get('error')]),
        'results': results
    }), 201


@assets_bp.route('/<asset_id>', methods=['PUT', 'POST'])
def update_asset(asset_id):
    """Update asset metadata."""
    logger.info(f"Updating asset: {asset_id}")
    db = current_app.config['database']
    asset = db.get_asset(asset_id)
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        asset.name = data['name']
    if 'description' in data:
        asset.description = data['description']
    if 'tags' in data:
        asset.tags = data['tags']
    if 'thumbnailUrl' in data:
        asset.thumbnail_url = data['thumbnailUrl']
    if 'hasParameters' in data:
        asset.has_parameters = data['hasParameters']
    if 'hasThumbnail' in data:
        asset.has_thumbnail = data['hasThumbnail']
    if 'hasBakedTextures' in data:
        asset.has_baked_textures = data['hasBakedTextures']
    
    from datetime import datetime
    asset.updated_at = datetime.utcnow()
    
    db.save_asset(asset)
    
    return jsonify(asset.to_dict())


@assets_bp.route('/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete an asset."""
    logger.info(f"Deleting asset: {asset_id}")
    db = current_app.config['database']
    storage = current_app.config['storage']
    
    asset = db.get_asset(asset_id)
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Delete source file
    if asset.storage_path:
        storage.delete_file(asset.storage_path)
        logger.info(f"Deleted source file: {asset.storage_path}")
    
    # Delete texture files
    textures = db.get_textures_for_asset(asset_id)
    for texture in textures:
        storage.delete_file(texture.storage_path)
    
    # Delete from database
    db.delete_asset(asset_id)
    
    logger.info(f"Asset deleted: {asset_id}")
    return jsonify({'success': True})


@assets_bp.route('/search', methods=['GET'])
def search_assets():
    """Search assets."""
    query = request.args.get('query', '')
    tags = request.args.getlist('tags')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    
    db = current_app.config['database']
    assets, total = db.get_assets(
        page=page,
        page_size=page_size,
        search=query if query else None,
        tags=tags if tags else None
    )
    
    items = []
    for asset in assets:
        asset_dict = asset.to_dict()
        textures = db.get_textures_for_asset(asset.id)
        asset_dict['textures'] = [t.to_dict() for t in textures]
        items.append(asset_dict)
    
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'pageSize': page_size,
        'totalPages': (total + page_size - 1) // page_size
    })


@assets_bp.route('/<asset_id>/generate-thumbnail', methods=['POST'])
def generate_asset_thumbnail(asset_id):
    """Generate thumbnail for an asset."""
    logger.info(f"Generating thumbnail for asset: {asset_id}")
    
    db = current_app.config['database']
    storage = current_app.config['storage']
    
    asset = db.get_asset(asset_id)
    if not asset:
        logger.error(f"Asset not found: {asset_id}")
        return jsonify({'error': 'Asset not found'}), 404
    
    if not asset.storage_path:
        logger.error(f"No storage path for asset: {asset_id}")
        return jsonify({'error': 'Source file path not set'}), 404
    
    if not Path(asset.storage_path).exists():
        logger.error(f"Source file not found: {asset.storage_path}")
        return jsonify({'error': f'Source file not found: {asset.storage_path}'}), 404
    
    data = request.get_json() or {}
    resolution = data.get('resolution', 256)
    
    try:
        # Import from the correct path
        from thumbnail.renderer import ThumbnailRenderer
        
        logger.info(f"Rendering thumbnail from: {asset.storage_path}")
        
        renderer = ThumbnailRenderer()
        result = renderer.render(
            filepath=asset.storage_path,
            resolution=resolution,
            output_format='png'
        )
        
        if not result.success:
            logger.error(f"Render failed: {result.error}")
            return jsonify({'error': _parse_sbscooker_error(result.error)}), 500
        
        logger.info(f"Thumbnail rendered: {result.output_path}")
        
        # Save thumbnail to storage
        thumb_storage_path, thumb_url = storage.save_file(
            result.output_path,
            f"{asset.id}_thumbnail.png",
            asset.id
        )
        
        logger.info(f"Thumbnail saved: {thumb_url}")
        
        # Update asset
        asset.thumbnail_url = thumb_url
        asset.has_thumbnail = True
        
        from datetime import datetime
        asset.updated_at = datetime.utcnow()
        
        db.save_asset(asset)
        
        return jsonify({
            'success': True,
            'thumbnailUrl': thumb_url,
            'asset': asset.to_dict()
        })
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({'error': f'Module import error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@assets_bp.route('/<asset_id>/extract-parameters', methods=['POST'])
def extract_asset_parameters(asset_id):
    """Extract parameters from an asset's source file."""
    logger.info(f"Extracting parameters for asset: {asset_id}")
    
    db = current_app.config['database']
    
    asset = db.get_asset(asset_id)
    if not asset:
        logger.error(f"Asset not found: {asset_id}")
        return jsonify({'error': 'Asset not found'}), 404
    
    if not asset.storage_path:
        logger.error(f"No storage path for asset: {asset_id}")
        return jsonify({'error': 'Source file path not set'}), 404
    
    if not Path(asset.storage_path).exists():
        logger.error(f"Source file not found: {asset.storage_path}")
        return jsonify({'error': f'Source file not found: {asset.storage_path}'}), 404
    
    try:
        # Import parameter extractor
        from extractor.extractor import ParameterExtractor
        
        logger.info(f"Extracting parameters from: {asset.storage_path}")
        
        extractor = ParameterExtractor()
        result = extractor.extract(asset.storage_path)
        
        if not result.get('success', False):
            error = result.get('error', 'Unknown error')
            logger.error(f"Extraction failed: {error}")
            return jsonify({'error': _parse_sbscooker_error(error)}), 500
        
        logger.info(f"Parameters extracted successfully")
        
        # Update asset with extracted parameters in metadata
        asset.has_parameters = True
        
        # Store parameters in asset metadata
        if asset.metadata is None:
            asset.metadata = {}
        asset.metadata['parameters'] = result.get('data', {})
        
        from datetime import datetime
        asset.updated_at = datetime.utcnow()
        
        db.save_asset(asset)
        
        return jsonify({
            'success': True,
            'parameters': result.get('data', {}),
            'asset': asset.to_dict()
        })
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({'error': f'Module import error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
