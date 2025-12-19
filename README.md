# Trading Journal - Offline Self-Hosted Application

A professional trading journal application for tracking and analyzing your trades, designed to run completely offline.

## Features

- **CSV Import**: Upload Fidelity trade exports with automatic duplicate detection
- **Auto-Matching**: FIFO algorithm automatically matches Buy→Sell pairs
- **Comprehensive Dashboard**: 16+ metrics including Win Rate, P&L, Hold Times, Consecutive Wins/Losses
- **Calendar View**: Monthly calendar with color-coded P&L (Green/Red)
- **Trades Journal**: Complete trade history with sortable columns
- **Reports & Analytics**: P&L trends, time-based performance analysis
- **CSV Storage**: All data stored in portable CSV files

## Requirements

- Python 3.8+
- Node.js 16+
- MongoDB (optional, not used in current version)

## Installation & Setup

### 1. Download This Application

```bash
# If you have this running on Emergent, download the entire /app directory
# Or clone from your repository
cd /path/to/trading-journal
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
yarn install
# or: npm install
```

### 4. Configuration

Edit `.env` files if needed:

**backend/.env**:
```
CORS_ORIGINS=*
```

**frontend/.env**:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Running the Application

### Option 1: Manual Start (Recommended for Development)

**Terminal 1 - Start Backend**:
```bash
cd backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Terminal 2 - Start Frontend**:
```bash
cd frontend
yarn start
# or: npm start
```

Application will open at `http://localhost:3000`

### Option 2: Production Build

**Build Frontend**:
```bash
cd frontend
yarn build
# Serve the build folder with any static server
```

**Run Backend**:
```bash
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001
```

## Usage

1. **Import Trades**: Click "Import CSV" and upload your Fidelity trade export
2. **View Dashboard**: See comprehensive trading metrics
3. **Check Calendar**: View daily P&L with color coding
4. **Analyze Reports**: Review P&L trends and time-based performance
5. **Browse Trades**: Sort and filter your complete trade history

## Data Storage

All trade data is stored in CSV files:
- `/app/data/raw_imports.csv` - All imported raw trades
- `/app/data/trades.csv` - Matched trade pairs with calculated metrics

**Backup Your Data**: Simply copy the `/app/data` folder to backup all your trading history.

## Offline Usage

This application runs 100% offline once installed:
- No internet connection required
- All data stored locally in CSV files
- Can be run on any computer with Python and Node.js

## Sharing Your Setup

To move this to another computer:
1. Copy the entire application folder
2. Copy the `/app/data` folder (your trade data)
3. Follow installation steps on the new computer
4. Run the application

## Troubleshooting

**Backend won't start**:
- Check Python version: `python --version` (needs 3.8+)
- Reinstall dependencies: `pip install -r requirements.txt`

**Frontend won't start**:
- Check Node version: `node --version` (needs 16+)
- Clear cache: `rm -rf node_modules && yarn install`

**Import fails**:
- Ensure CSV is in Fidelity export format
- Check that file has Symbol, Action, Status, Amount, and Order Time columns

## Support

For issues or questions, check the logs:
- Backend: Check terminal output
- Frontend: Check browser console (F12)

---

**Built with**: FastAPI (Python) + React + CSV Storage

**Self-Hosted & Offline-First** - Your data stays on your machine.
