#!/usr/bin/env python3
"""
SAT Thumbnail CLI

Command-line interface for thumbnail generation.

Usage:
    python -m sat_tools.thumbnail.cli generate <file> [--output <path>] [--resolution <size>]
    python -m sat_tools.thumbnail.cli batch <directory> [--output <dir>] [--recursive]
    python -m sat_tools.thumbnail.cli read-metadata <image>
"""

import argparse
import sys
import json
from pathlib import Path


def cmd_generate(args):
    """Generate a thumbnail for a single file."""
    from .renderer import ThumbnailRenderer
    from .metadata import ThumbnailMetadata, MetadataWriter
    
    filepath = args.file
    output = args.output
    resolution = args.resolution
    
    print(f"Generating thumbnail for: {filepath}")
    print(f"Resolution: {resolution}x{resolution}")
    
    try:
        renderer = ThumbnailRenderer(args.sat_path)
        result = renderer.render(
            filepath=filepath,
            output_path=output,
            resolution=resolution,
            output_format='png'
        )
        
        if result.success:
            print(f"Generated: {result.output_path}")
            
            # Embed metadata
            if not args.no_metadata:
                metadata = ThumbnailMetadata.create(
                    source_file=filepath,
                    graph_name=result.graph_name,
                    resolution=result.resolution,
                    tags=args.tags.split(',') if args.tags else []
                )
                writer = MetadataWriter()
                writer.write(result.output_path, metadata)
                print("Metadata embedded successfully")
            
            return 0
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_batch(args):
    """Batch generate thumbnails."""
    from .batch import BatchProcessor
    
    directory = args.directory
    output_dir = args.output or directory
    resolution = args.resolution
    recursive = args.recursive
    
    print(f"Batch processing: {directory}")
    print(f"Output directory: {output_dir}")
    print(f"Recursive: {recursive}")
    
    try:
        processor = BatchProcessor(args.sat_path)
        
        def progress(current, total, filename):
            print(f"  [{current}/{total}] {filename}")
        
        result = processor.process_directory(
            directory=directory,
            output_dir=output_dir,
            resolution=resolution,
            recursive=recursive,
            embed_metadata=not args.no_metadata,
            tags=args.tags.split(',') if args.tags else None,
            progress_callback=progress
        )
        
        print(f"\nComplete:")
        print(f"  Total: {result.total}")
        print(f"  Success: {result.success}")
        print(f"  Failed: {result.failed}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  {error['file']}: {error['error']}")
        
        return 0 if result.failed == 0 else 1
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_read_metadata(args):
    """Read metadata from a thumbnail image."""
    from .metadata import MetadataReader
    
    image_path = args.image
    
    try:
        reader = MetadataReader()
        metadata = reader.read(image_path)
        
        if metadata:
            print("Metadata found:")
            print(json.dumps(metadata.to_dict(), indent=2))
        else:
            print("No SAT metadata found in image.")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='sat-thumbnail',
        description='SAT Thumbnail Generator'
    )
    parser.add_argument('--sat-path', help='Path to SAT installation')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate thumbnail for a file')
    gen_parser.add_argument('file', help='Path to SBS/SBSAR file')
    gen_parser.add_argument('-o', '--output', help='Output path')
    gen_parser.add_argument('-r', '--resolution', type=int, default=256,
                           help='Output resolution (default: 256)')
    gen_parser.add_argument('--no-metadata', action='store_true',
                           help='Do not embed metadata')
    gen_parser.add_argument('--tags', help='Comma-separated tags')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch generate thumbnails')
    batch_parser.add_argument('directory', help='Directory with SBS/SBSAR files')
    batch_parser.add_argument('-o', '--output', help='Output directory')
    batch_parser.add_argument('-r', '--resolution', type=int, default=256,
                             help='Output resolution')
    batch_parser.add_argument('--recursive', action='store_true',
                             help='Search recursively')
    batch_parser.add_argument('--no-metadata', action='store_true',
                             help='Do not embed metadata')
    batch_parser.add_argument('--tags', help='Comma-separated tags')
    
    # Read metadata command
    read_parser = subparsers.add_parser('read-metadata', help='Read metadata from image')
    read_parser.add_argument('image', help='Path to PNG image')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'batch':
        return cmd_batch(args)
    elif args.command == 'read-metadata':
        return cmd_read_metadata(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
