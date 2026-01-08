#!/usr/bin/env python3
"""
SAT Parameter Extractor CLI

Command-line interface for extracting parameters from SBS/SBSAR files.

Usage:
    python -m sat_tools.extractor.cli extract <file> [--output <path>]
    python -m sat_tools.extractor.cli batch <directory> [--output <dir>] [--recursive]
    python -m sat_tools.extractor.cli schema [--example]
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List
import json


def find_substance_files(directory: str, recursive: bool = False) -> List[Path]:
    """Find all SBS and SBSAR files in a directory."""
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    patterns = ['*.sbs', '*.sbsar']
    files = []
    
    for pattern in patterns:
        if recursive:
            files.extend(path.rglob(pattern))
        else:
            files.extend(path.glob(pattern))
    
    return sorted(files)


def cmd_extract(args):
    """Extract parameters from a single file."""
    from .extractor import ParameterExtractor
    
    filepath = args.file
    output = args.output
    
    print(f"Extracting parameters from: {filepath}")
    
    try:
        extractor = ParameterExtractor(args.sat_path)
        result = extractor.extract(filepath)
        
        if output:
            output_path = output
        else:
            output_path = str(Path(filepath).with_suffix('.json'))
        
        result.save(output_path)
        print(f"Saved to: {output_path}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"  File: {result.filename}")
        print(f"  Type: {result.file_type}")
        print(f"  Graphs: {len(result.graphs)}")
        total_nodes = sum(len(g.nodes) for g in result.graphs)
        print(f"  Total Nodes: {total_nodes}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def cmd_batch(args):
    """Batch extract parameters from a directory."""
    from .extractor import ParameterExtractor
    
    directory = args.directory
    output_dir = args.output or directory
    recursive = args.recursive
    
    print(f"Scanning directory: {directory}")
    print(f"Recursive: {recursive}")
    
    try:
        files = find_substance_files(directory, recursive)
        
        if not files:
            print("No SBS/SBSAR files found.")
            return 0
        
        print(f"Found {len(files)} files")
        
        extractor = ParameterExtractor(args.sat_path)
        
        success_count = 0
        error_count = 0
        
        for filepath in files:
            print(f"\nProcessing: {filepath.name}")
            
            try:
                result = extractor.extract(str(filepath))
                
                # Determine output path
                rel_path = filepath.relative_to(directory) if filepath.is_relative_to(directory) else filepath
                output_path = Path(output_dir) / rel_path.with_suffix('.json')
                
                # Create output directory if needed
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                result.save(str(output_path))
                print(f"  -> {output_path}")
                success_count += 1
                
            except Exception as e:
                print(f"  Error: {e}", file=sys.stderr)
                error_count += 1
        
        print(f"\nComplete: {success_count} succeeded, {error_count} failed")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def cmd_schema(args):
    """Display or save the JSON schema."""
    from .schema import ParameterSchema
    
    if args.example:
        data = ParameterSchema.generate_example()
        print("Example parameter file:")
    else:
        data = ParameterSchema.get_schema()
        print("JSON Schema for parameter files:")
    
    print(json.dumps(data, indent=2))
    
    if args.save:
        with open(args.save, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved to: {args.save}")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='sat-extractor',
        description='SAT Parameter Extractor - Extract parameters from SBS/SBSAR files'
    )
    parser.add_argument('--sat-path', help='Path to SAT installation')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract from a single file')
    extract_parser.add_argument('file', help='Path to SBS/SBSAR file')
    extract_parser.add_argument('-o', '--output', help='Output JSON file path')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch extract from directory')
    batch_parser.add_argument('directory', help='Directory containing SBS/SBSAR files')
    batch_parser.add_argument('-o', '--output', help='Output directory')
    batch_parser.add_argument('-r', '--recursive', action='store_true',
                             help='Recursively search subdirectories')
    
    # Schema command
    schema_parser = subparsers.add_parser('schema', help='Display JSON schema')
    schema_parser.add_argument('--example', action='store_true',
                              help='Show example instead of schema')
    schema_parser.add_argument('--save', help='Save to file')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        return cmd_extract(args)
    elif args.command == 'batch':
        return cmd_batch(args)
    elif args.command == 'schema':
        return cmd_schema(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
