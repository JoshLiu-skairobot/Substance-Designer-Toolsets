# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **SAT (Substance Automation Toolkit) plugin development project** for building headless server automation tools. The project uses the Substance Automation Toolkit API located in `Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/` to create Python-based automation scripts for server deployment.

**Important**: SAT API includes both command-line tools AND the pysbs Python API. Both can be used for automation.

**Official Documentation**:
- Index page: https://helpx.adobe.com/substance-3d-sat.html
- Full documentation: Extract `Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/html-doc.zip`
- SAT Cookbook: Available in official documentation for recipes and examples

## Environment Setup

### Critical Environment Variables

Set `SDAPI_SATPATH` to point to the SAT installation directory:

```bash
# Windows (typically auto-detected, but can override)
set SDAPI_SATPATH=E:\Substance Automatic Toolset Dev\Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe

# Linux/macOS
export SDAPI_SATPATH="/path/to/Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe"
```

Optional environment variables:
- `SDAPI_SATPACKAGESPATH` - Path to resource packages
- `SDAPI_SATSAMPLESPATH` - Path to sample files

### Python Environment

**Required**: Python 3.x (Python 2.7 is also supported but deprecated)

**Install pysbs API**:
```bash
pip install "Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/Python API/Pysbs-2025.0.3-py2.py3-none-win_amd64.whl"
```

## Common SAT Commands (Headless Server Usage)

### 1. Render SBSAR to Textures

```bash
# Basic rendering
sbsrender render --inputs <file.sbsar> --output-path <output_dir>

# With resolution control
sbsrender render --inputs <file.sbsar> --set-value "$outputsize@10,10" --output-path <output_dir>

# Get SBSAR info
sbsrender info --inputs <file.sbsar>
```

### 2. Cook SBS to SBSAR

```bash
# Basic cooking
sbscooker --inputs <file.sbs> --output-path <output_dir>

# With includes path
sbscooker --inputs <file.sbs> --includes <resource_path> --output-path <output_dir>
```

### 3. Bake Textures from Meshes

```bash
# Bake normal map
substance3d_baker Normal.Raytraced --high-poly <high.fbx> --low-poly <low.fbx> --output <output_dir>

# Bake ambient occlusion
substance3d_baker AmbientOcclusion.Raytraced --mesh <mesh.fbx> --output <output_dir>

# Bake curvature
substance3d_baker Curvature.Raytraced --mesh <mesh.fbx> --output <output_dir>

# List all baking presets
substance3d_baker --list-bakers
```

### 4. Edit/Export SBS Files

```bash
# Export SBS with dependencies
sbsmutator export --input <file.sbs> --output-path <output_dir>

# Get SBS info
sbsmutator info --input <file.sbs>

# Update SBS to latest format
sbsmutator update --input <file.sbs> --output-path <output_dir>
```

### 5. Global Options (All Tools)

```bash
--help              # Show help
--help-advanced     # Show all options
--verbose, -v       # Enable detailed logging
--quiet, -q         # Suppress warnings
--version, -V       # Show version
```

## Python Automation Patterns

### Pattern 1: Command-Line Tool Invocation (Recommended for Headless)

Use subprocess to call SAT command-line tools:

```python
import subprocess

def render_sbsar(sbsrender_path, sbsar_file, output_path, resolution="10,10"):
    cmd = [
        sbsrender_path,
        "render",
        "--inputs", sbsar_file,
        "--set-value", f"$outputsize@{resolution}",
        "--output-path", output_path
    ]
    subprocess.run(cmd, check=True)

def cook_sbs(sbscooker_path, sbs_file, output_path):
    cmd = [sbscooker_path, "--inputs", sbs_file, "--output-path", output_path]
    subprocess.run(cmd, check=True)
```

### Pattern 2: Using pysbs API (For Graph Manipulation)

```python
from pysbs import context, batchtools

# Initialize context
ctx = context.Context()

# Use pysbs for graph creation/editing
# (See samples/scripts/ for examples)
```

### Pattern 3: Multi-threaded Batch Processing

See `Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/samples/scripts/batchtools_utilities.py` for reference implementation using threading and queue for parallel processing.

## Architecture Overview

### SAT API Components

1. **Command-Line Executables** (Headless-ready):
   - `sbsrender.exe` - Render SBSAR to bitmaps
   - `sbscooker.exe` - Cook SBS to SBSAR
   - `sbsmutator.exe` - Edit/export SBS files
   - `substance3d_baker.exe` - Bake textures from meshes (maps for meshes)
   - `sbsupdater.exe` - Update Substance files to latest format
   - `mdltools.exe` - MDL (Material Definition Language) file operations
   - `axftools.exe` - AXF (Allegorithmic Exchange Format) file operations
   - `psdparse.exe` - PSD file parsing utility
   - `spotcolorinfo.exe` - Spot color information tool

2. **Python API (pysbs)**:
   - Located: `Python API/Pysbs-2025.0.3-py2.py3-none-win_amd64.whl`
   - Modules: `context`, `batchtools`, `sbsgenerator`, `sbsenum`, `autograph`

3. **Resources**:
   - `resources/packages/` - Substance material packages
   - `resources/templates/` - Material templates
   - `resources/ocio/` - Color management configs

### Typical Automation Pipeline

```
Input 3D Mesh (FBX/OBJ)
    ↓
[substance3d_baker] Bake maps (Normal, AO, Curvature, etc.)
    ↓
[pysbs or manual] Create/edit SBS material
    ↓
[sbscooker] Cook SBS → SBSAR
    ↓
[sbsrender] Render final textures
    ↓
Output Textures (BaseColor, Roughness, Metallic, Normal, Height)
```

### Design Considerations for Server Deployment

1. **Use subprocess for reliability**: Call command-line tools via subprocess rather than importing everything into Python
2. **Process isolation**: Each SAT tool runs in its own process
3. **Parallel processing**: Use threading/multiprocessing for batch operations
4. **Path resolution**: Always use absolute paths or properly resolve via SDAPI_SATPATH
5. **Error handling**: Check return codes from subprocess calls
6. **Logging**: Use `--verbose` flag for debugging, `--quiet` for production

## Sample Scripts Reference

Located in `Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/samples/scripts/`:

- **`batchtools_utilities.py`** - Core utility functions for batch operations (REFERENCE THIS)
- **`demos.py`** - Usage examples of SAT tools
- **`demo_texturing_template.py`** - Complete texturing pipeline example
- **`variations.py`** - Material variation generation
- **`create_compositing_network.py`** - Programmatic graph creation with pysbs

## Development Workflow

### Running Sample Scripts

```bash
# Set environment variable
export SDAPI_SATPATH="/path/to/SAT"

# Run demos
python Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/samples/scripts/demos.py

# Run texturing template
python Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/samples/scripts/demo_texturing_template.py
```

### Testing Command-Line Tools

Test tools individually before building automation:

```bash
# Verify sbsrender works
./Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/sbsrender --version

# Test render on sample
./Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/sbsrender render \
  --inputs "Substance_Automation_Toolkit_Pro-15.0.3-2112-msvc14-x64-adobe/samples/content/Sbsar/Example.sbsar" \
  --output-path ./output
```

## Critical Notes for Plugin Development

1. **Always set SDAPI_SATPATH** before running any SAT tool
2. **Use absolute paths** when calling SAT executables in production
3. **Reference batchtools_utilities.py** for subprocess invocation patterns
4. **For headless servers**: Prefer command-line tools over pysbs when possible (better isolation)
5. **For graph manipulation**: Use pysbs API when you need to programmatically create/edit SBS graphs
6. **Thread-safe operations**: Each SAT command-line tool invocation is isolated and thread-safe
