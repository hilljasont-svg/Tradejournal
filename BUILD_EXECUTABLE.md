# Building Trading Journal Executable

This guide will help you create a standalone executable that runs without Python or Node.js installed.

## Prerequisites

1. Python 3.8+ installed
2. Node.js 16+ installed
3. This project downloaded from GitHub

## Quick Start

### Windows
```bash
cd /path/to/trading-journal
python build_executable.py
```

Executable will be in `dist/TradingJournal/TradingJournal.exe`

### Mac/Linux
```bash
cd /path/to/trading-journal
python3 build_executable.py
```

Executable will be in `dist/TradingJournal/TradingJournal` (or `.app` on Mac)

## Step-by-Step Instructions

### Step 1: Download Your Code

1. Connect GitHub in Emergent platform
2. Click "Save to GitHub"
3. Go to your GitHub repo
4. Click "Code" → "Download ZIP"
5. Extract to a folder

### Step 2: Build Frontend

```bash
cd frontend
yarn install
yarn build
```

This creates a `frontend/build` folder with static files.

### Step 3: Install PyInstaller

```bash
cd ../backend
pip install pyinstaller
```

### Step 4: Run Build Script

```bash
# From project root
python build_executable.py
```

The script will:
- Build the React frontend
- Copy static files to backend
- Configure FastAPI to serve static files
- Bundle everything with PyInstaller
- Create executable in `dist/TradingJournal/`

### Step 5: Test the Executable

**Windows:**
```bash
cd dist\TradingJournal
TradingJournal.exe
```

**Mac/Linux:**
```bash
cd dist/TradingJournal
./TradingJournal
```

Your browser should open to `http://localhost:8001`

## What Gets Bundled

✅ FastAPI backend
✅ React frontend (built static files)
✅ All Python dependencies
✅ CSV data storage
✅ Everything needed to run offline

## Executable Size

Expect **50-100MB** depending on your platform:
- Windows: ~70MB
- Mac: ~80MB
- Linux: ~60MB

## Distribution

### To Share With Others:

1. Zip the entire `dist/TradingJournal` folder
2. Share the zip file
3. Recipients just unzip and double-click the executable
4. No installation needed!

### Creating for Multiple Platforms:

You need to build on each platform:
- Build on Windows → creates `.exe`
- Build on Mac → creates `.app`
- Build on Linux → creates binary

**Cannot cross-compile!** (Windows build won't run on Mac)

## Data Location

The executable stores data in:
- **Windows:** `C:\Users\YourName\AppData\Local\TradingJournal\data`
- **Mac:** `~/Library/Application Support/TradingJournal/data`
- **Linux:** `~/.local/share/TradingJournal/data`

Your CSV files are stored there for persistence.

## Troubleshooting

### "Module not found" error
```bash
cd backend
pip install -r requirements.txt
pyinstaller server.spec --clean
```

### Frontend not showing
Check that `frontend/build` exists:
```bash
ls frontend/build
```

If empty, rebuild:
```bash
cd frontend
yarn build
```

### Executable won't start
- Run from terminal to see errors
- Check antivirus isn't blocking it
- Try running as administrator (Windows)

### Port 8001 already in use
Edit `server.py` to use different port:
```python
uvicorn.run(app, host="0.0.0.0", port=8002)
```

## Advanced: Customizing the Build

### Change App Name
Edit `build_executable.py`:
```python
name='MyTradingJournal'
```

### Add Icon
1. Create `icon.ico` (Windows) or `icon.icns` (Mac)
2. Edit `build_executable.py`:
```python
icon='icon.ico'
```

### Reduce Size
Edit PyInstaller options:
```python
--exclude-module matplotlib
--exclude-module PIL
```

## Notes

- First run takes 5-10 seconds to start (loading Python)
- Subsequent runs are faster (3-5 seconds)
- Browser opens automatically
- Close browser tab, but keep terminal open
- Press Ctrl+C in terminal to stop server
- Data persists between runs

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run from terminal to see error messages
3. Verify all prerequisites are installed
4. Try rebuilding from scratch
