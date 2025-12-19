#!/usr/bin/env python3
"""
Build script for creating Trading Journal standalone executable

Usage:
    python build_executable.py

Requirements:
    - Python 3.8+
    - Node.js & Yarn
    - PyInstaller (installed automatically)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

def run_command(cmd, cwd=None):
    """Run shell command and handle errors"""
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    print(result.stdout)
    return True

def step(number, description):
    """Print step header"""
    print(f"\n{'='*60}")
    print(f"STEP {number}: {description}")
    print(f"{'='*60}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        Trading Journal - Executable Builder              ║
    ║                                                           ║
    ║  This will create a standalone executable that runs      ║
    ║  without Python or Node.js installed.                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Step 1: Check prerequisites
    step(1, "Checking Prerequisites")
    
    # Check Python
    python_version = sys.version_info
    print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 8):
        print("ERROR: Python 3.8+ required")
        return False
    
    # Check Node.js
    if not run_command("node --version"):
        print("ERROR: Node.js not found. Please install Node.js 16+")
        return False
    
    # Check Yarn
    if not run_command("yarn --version"):
        print("Installing Yarn...")
        run_command("npm install -g yarn")
    
    # Step 2: Install backend dependencies
    step(2, "Installing Backend Dependencies")
    if not run_command("pip install -r requirements.txt", cwd=BACKEND_DIR):
        print("ERROR: Failed to install backend dependencies")
        return False
    
    # Install PyInstaller
    if not run_command("pip install pyinstaller"):
        print("ERROR: Failed to install PyInstaller")
        return False
    
    # Step 3: Build Frontend
    step(3, "Building React Frontend")
    
    print("Installing frontend dependencies...")
    if not run_command("yarn install", cwd=FRONTEND_DIR):
        print("ERROR: Failed to install frontend dependencies")
        return False
    
    print("Building production bundle...")
    if not run_command("yarn build", cwd=FRONTEND_DIR):
        print("ERROR: Failed to build frontend")
        return False
    
    # Step 4: Prepare backend to serve static files
    step(4, "Configuring Backend for Static Files")
    
    # Copy built frontend to backend
    static_dir = BACKEND_DIR / "static"
    if static_dir.exists():
        shutil.rmtree(static_dir)
    
    frontend_build = FRONTEND_DIR / "build"
    if not frontend_build.exists():
        print("ERROR: Frontend build directory not found")
        return False
    
    shutil.copytree(frontend_build, static_dir)
    print(f"✓ Copied frontend to {static_dir}")
    
    # Create modified server.py that serves static files
    server_py = BACKEND_DIR / "server.py"
    server_standalone = BACKEND_DIR / "server_standalone.py"
    
    with open(server_py, 'r') as f:
        server_code = f.read()
    
    # Add static file serving
    static_serving = '''
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import webbrowser
import threading

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = Path("static") / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse("static/index.html")

if __name__ == "__main__":
    # Open browser after a short delay
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8001")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("""\n    ╔═══════════════════════════════════════════════════════════╗
    ║           Trading Journal - Running...                    ║
    ║                                                           ║
    ║  → Opening browser at http://localhost:8001               ║
    ║  → Press Ctrl+C to stop the server                       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
'''
    
    with open(server_standalone, 'w') as f:
        f.write(server_code + "\n" + static_serving)
    
    print("✓ Created standalone server configuration")
    
    # Step 5: Create PyInstaller spec file
    step(5, "Creating PyInstaller Configuration")
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['server_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TradingJournal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TradingJournal',
)
'''
    
    spec_file = BACKEND_DIR / "TradingJournal.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print("✓ Created PyInstaller spec file")
    
    # Step 6: Build with PyInstaller
    step(6, "Building Executable (this may take 2-5 minutes)")
    
    if not run_command("pyinstaller TradingJournal.spec --clean", cwd=BACKEND_DIR):
        print("ERROR: Failed to build executable")
        return False
    
    # Step 7: Copy to project dist folder
    step(7, "Finalizing Build")
    
    backend_dist = BACKEND_DIR / "dist" / "TradingJournal"
    project_dist = DIST_DIR / "TradingJournal"
    
    if project_dist.exists():
        shutil.rmtree(project_dist)
    
    shutil.copytree(backend_dist, project_dist)
    print(f"✓ Executable created at: {project_dist}")
    
    # Create data directory
    data_dir = project_dist / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"✓ Created data directory at: {data_dir}")
    
    # Create README
    readme = project_dist / "README.txt"
    with open(readme, 'w') as f:
        f.write('''Trading Journal - Standalone Executable

To run:
  Windows: Double-click TradingJournal.exe
  Mac/Linux: ./TradingJournal

The application will:
1. Start a local server on port 8001
2. Automatically open your browser
3. You can start importing and analyzing your trades!

To stop:
  Press Ctrl+C in the terminal window

Data Storage:
  Your trade data is stored in the 'data' folder
  Backup this folder to preserve your trading history

Note:
  - First launch may take 5-10 seconds
  - Your antivirus might flag it (it's safe, just add exception)
  - Keep the terminal window open while using the app
''')
    
    print("✓ Created README.txt")
    
    # Success!
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              BUILD SUCCESSFUL! 🎉                         ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Your executable is ready at:
    {}
    
    To run:
    {}  
    
    To distribute:
    Zip the entire 'TradingJournal' folder and share it.
    Recipients can extract and run without any installation!
    
    Executable size: ~50-100MB
    
    """.format(
        project_dist,
        "  > cd dist/TradingJournal\n  > TradingJournal.exe" if sys.platform == "win32" else "  > cd dist/TradingJournal\n  > ./TradingJournal"
    ))
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
