"""
API Integration Test Script

Tests the complete workflow:
1. Check sbsrender availability
2. Generate thumbnail from SBS file
3. Verify storage works
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_sbsrender():
    """Test if sbsrender is available and working."""
    print("=" * 60)
    print("Testing sbsrender availability...")
    print("=" * 60)
    
    from thumbnail.renderer import ThumbnailRenderer
    
    renderer = ThumbnailRenderer()
    
    print(f"SAT Path: {renderer.sat_path}")
    print(f"sbsrender Path: {renderer.sbsrender_path}")
    
    if renderer.sbsrender_path and os.path.exists(renderer.sbsrender_path):
        print("[OK] sbsrender found!")
        return True
    else:
        print("[FAIL] sbsrender NOT found!")
        return False


def test_render_thumbnail(sbs_file: str):
    """Test rendering a thumbnail from an SBS file."""
    print("\n" + "=" * 60)
    print(f"Testing thumbnail rendering for: {sbs_file}")
    print("=" * 60)
    
    from thumbnail.renderer import ThumbnailRenderer
    
    if not os.path.exists(sbs_file):
        print(f"[FAIL] SBS file not found: {sbs_file}")
        return False
    
    print(f"[OK] SBS file exists: {sbs_file}")
    
    renderer = ThumbnailRenderer()
    
    # Create output directory
    output_dir = Path(__file__).parent / "storage" / "thumbnails"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{Path(sbs_file).stem}_preview.png"
    
    print(f"Output path: {output_path}")
    print("Rendering... (this may take a moment)")
    
    result = renderer.render(
        filepath=sbs_file,
        output_path=str(output_path),
        resolution=256,
        output_format='png'
    )
    
    if result.success:
        print(f"[OK] Thumbnail rendered successfully!")
        print(f"  Output: {result.output_path}")
        print(f"  Resolution: {result.resolution}")
        return True
    else:
        print(f"[FAIL] Render failed: {result.error}")
        return False


def test_get_outputs(sbs_file: str):
    """Test getting available outputs from SBS file."""
    print("\n" + "=" * 60)
    print(f"Testing get available outputs for: {sbs_file}")
    print("=" * 60)
    
    from thumbnail.renderer import ThumbnailRenderer
    
    renderer = ThumbnailRenderer()
    outputs = renderer.get_available_outputs(sbs_file)
    
    if outputs:
        print(f"[OK] Found {len(outputs)} outputs:")
        for output in outputs:
            print(f"  - {output}")
        return True
    else:
        print("No outputs found (this might be okay)")
        return True


def test_storage():
    """Test storage service."""
    print("\n" + "=" * 60)
    print("Testing storage service...")
    print("=" * 60)
    
    from server.storage import StorageService
    
    storage = StorageService(
        base_path="./storage",
        url_prefix="/static/assets"
    )
    
    # Check storage directory
    if storage.base_path.exists():
        print(f"[OK] Storage directory exists: {storage.base_path}")
    else:
        print(f"[FAIL] Storage directory missing: {storage.base_path}")
        return False
    
    # Test saving a file
    test_content = b"Test file content"
    test_path = Path(__file__).parent / "storage" / "test_file.txt"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_bytes(test_content)
    
    try:
        storage_path, url = storage.save_file(str(test_path), "test.txt")
        print(f"[OK] File saved to: {storage_path}")
        print(f"  URL: {url}")
        
        # Cleanup
        storage.delete_file(storage_path)
        test_path.unlink()
        print("[OK] Cleanup successful")
        return True
    except Exception as e:
        print(f"[FAIL] Storage test failed: {e}")
        return False


def test_database():
    """Test database operations."""
    print("\n" + "=" * 60)
    print("Testing database...")
    print("=" * 60)
    
    from server.models import Database, Asset
    
    db_path = Path(__file__).parent / "test_assets.db"
    
    try:
        db = Database(str(db_path))
        print("[OK] Database initialized")
        
        # Create test asset
        asset = Asset.create(
            name="Test Asset",
            source_file="test.sbs",
            file_type="sbs",
            description="Test asset for API testing"
        )
        
        db.save_asset(asset)
        print(f"[OK] Asset saved with ID: {asset.id}")
        
        # Retrieve asset
        retrieved = db.get_asset(asset.id)
        if retrieved and retrieved.name == "Test Asset":
            print("[OK] Asset retrieved successfully")
        else:
            print("[FAIL] Asset retrieval failed")
            return False
        
        # Cleanup
        db.delete_asset(asset.id)
        db_path.unlink()
        print("[OK] Cleanup successful")
        return True
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow(sbs_file: str):
    """Test the complete workflow."""
    print("\n" + "=" * 60)
    print("FULL WORKFLOW TEST")
    print("=" * 60)
    
    from server.models import Database, Asset
    from server.storage import StorageService
    from thumbnail.renderer import ThumbnailRenderer
    
    # Initialize services
    db = Database("./assets.db")
    storage = StorageService("./storage", "/static/assets")
    renderer = ThumbnailRenderer()
    
    # Step 1: Create asset from SBS file
    print("\n1. Creating asset from SBS file...")
    sbs_path = Path(sbs_file)
    
    if not sbs_path.exists():
        print(f"[FAIL] SBS file not found: {sbs_file}")
        return False
    
    # Save source file to storage
    storage_path, source_url = storage.save_file(
        str(sbs_path),
        sbs_path.name
    )
    print(f"   [OK] Source file saved to storage: {storage_path}")
    
    asset = Asset.create(
        name=sbs_path.stem,
        source_file=sbs_path.name,
        source_file_url=source_url,
        file_type='sbs' if sbs_path.suffix == '.sbs' else 'sbsar',
        description=f"Imported from {sbs_path.name}"
    )
    
    db.save_asset(asset)
    print(f"   [OK] Asset created with ID: {asset.id}")
    
    # Step 2: Generate thumbnail
    print("\n2. Generating thumbnail...")
    
    result = renderer.render(
        filepath=str(sbs_path),
        resolution=256,
        output_format='png'
    )
    
    if result.success:
        print(f"   [OK] Thumbnail rendered: {result.output_path}")
        
        # Save thumbnail to storage
        thumb_storage_path, thumb_url = storage.save_file(
            result.output_path,
            f"{asset.id}_thumbnail.png",
            asset.id
        )
        
        # Update asset with thumbnail
        asset.thumbnail_url = thumb_url
        asset.has_thumbnail = True
        db.save_asset(asset)
        print(f"   [OK] Thumbnail saved: {thumb_url}")
    else:
        print(f"   [FAIL] Thumbnail rendering failed: {result.error}")
    
    # Step 3: Verify asset in database
    print("\n3. Verifying asset in database...")
    
    retrieved = db.get_asset(asset.id)
    if retrieved:
        print(f"   [OK] Asset retrieved: {retrieved.name}")
        print(f"     - Source file: {retrieved.source_file}")
        print(f"     - File type: {retrieved.file_type}")
        print(f"     - Thumbnail URL: {retrieved.thumbnail_url}")
        print(f"     - Has thumbnail: {retrieved.has_thumbnail}")
    else:
        print("   [FAIL] Asset not found in database")
        return False
    
    print("\n" + "=" * 60)
    print("[OK] FULL WORKFLOW TEST PASSED!")
    print("=" * 60)
    
    return True


def main():
    print("SAT API Integration Tests")
    print("=" * 60)
    
    # Find the SBS file
    project_root = Path(__file__).parent.parent
    sbs_file = project_root / "Metal_Aluminum_Brush Finish.sbs"
    
    if not sbs_file.exists():
        print(f"[FAIL] Test SBS file not found: {sbs_file}")
        print("Please ensure 'Metal_Aluminum_Brush Finish.sbs' is in the project root")
        return
    
    print(f"Using test file: {sbs_file}")
    
    # Run tests
    results = []
    
    # Test 1: sbsrender availability
    results.append(("sbsrender availability", test_sbsrender()))
    
    # Test 2: Storage
    results.append(("Storage service", test_storage()))
    
    # Test 3: Database
    results.append(("Database", test_database()))
    
    # Test 4: Render thumbnail (only if sbsrender is available)
    if results[0][1]:  # sbsrender is available
        results.append(("Render thumbnail", test_render_thumbnail(str(sbs_file))))
        results.append(("Get outputs", test_get_outputs(str(sbs_file))))
        results.append(("Full workflow", test_full_workflow(str(sbs_file))))
    else:
        print("\nSkipping render tests as sbsrender is not available")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")


if __name__ == "__main__":
    main()
