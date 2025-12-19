from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import csv
import io
from datetime import datetime, time
from collections import defaultdict

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(exist_ok=True)

TRADES_FILE = DATA_DIR / "trades.csv"
RAW_IMPORTS_FILE = DATA_DIR / "raw_imports.csv"

# Models
class TradeImportResponse(BaseModel):
    success: bool
    imported_count: int
    duplicate_count: int
    matched_trades_count: int
    message: str

class MatchedTrade(BaseModel):
    trade_date: str
    symbol: str
    side: str
    entry_action: str
    exit_action: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    result: str
    hold_time: str

class DashboardMetrics(BaseModel):
    total_pnl: float
    avg_daily_pnl: float
    avg_trade_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    scratch_trades: int
    win_rate: float
    loss_rate: float
    scratch_rate: float
    avg_winning_trade: float
    avg_losing_trade: float
    largest_gain: float
    largest_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    avg_hold_time_winning: str
    avg_hold_time_losing: str
    avg_hold_time_scratch: str

class CalendarDay(BaseModel):
    date: str
    pnl: float
    trade_count: int

def parse_fidelity_time(time_str: str) -> Optional[datetime]:
    """Parse Fidelity time format: '3:31:36 PM ET Dec-18-2025'"""
    try:
        parts = time_str.split(' ET ')
        if len(parts) != 2:
            return None
        time_part = parts[0]
        date_part = parts[1]
        
        datetime_str = f"{date_part} {time_part}"
        return datetime.strptime(datetime_str, "%b-%d-%Y %I:%M:%S %p")
    except:
        return None

def parse_price_from_status(status: str) -> Optional[float]:
    """Extract price from 'Filled at $2.75' format"""
    try:
        if 'Filled at $' in status:
            price_str = status.split('Filled at $')[1].split(',')[0].strip()
            return float(price_str)
    except:
        pass
    return None

def calculate_hold_time(entry_dt, exit_dt) -> str:
    """Calculate hold time in HH:MM:SS format"""
    # Handle string datetime conversion
    if isinstance(entry_dt, str):
        entry_dt = datetime.fromisoformat(entry_dt)
    if isinstance(exit_dt, str):
        exit_dt = datetime.fromisoformat(exit_dt)
    
    if not isinstance(entry_dt, datetime) or not isinstance(exit_dt, datetime):
        return "00:00:00"
    
    diff = exit_dt - entry_dt
    total_seconds = int(diff.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def match_trades(raw_trades: List[dict]) -> List[dict]:
    """Match Buy and Sell trades to create matched trade pairs"""
    # Group by symbol
    by_symbol = defaultdict(list)
    for trade in raw_trades:
        symbol = trade.get('Symbol', '').strip()
        if symbol:
            by_symbol[symbol].append(trade)
    
    matched_trades = []
    
    for symbol, trades in by_symbol.items():
        # Sort by order time
        trades.sort(key=lambda t: t.get('order_datetime', datetime.min))
        
        buy_stack = []
        sell_stack = []
        
        for trade in trades:
            action = trade.get('Action', '').lower()
            
            if 'buy' in action:
                buy_stack.append(trade)
            elif 'sell' in action:
                sell_stack.append(trade)
        
        # Match FIFO: First buy with first sell
        while buy_stack and sell_stack:
            buy_trade = buy_stack.pop(0)
            sell_trade = sell_stack.pop(0)
            
            entry_price = buy_trade.get('price')
            exit_price = sell_trade.get('price')
            quantity = buy_trade.get('Amount', 0)
            
            if entry_price and exit_price and quantity:
                pnl = (exit_price - entry_price) * quantity
                
                # Determine result
                if pnl > 5:
                    result = 'Win'
                elif pnl < -5:
                    result = 'Lose'
                else:
                    result = 'Scratch'
                
                entry_dt = buy_trade.get('order_datetime')
                exit_dt = sell_trade.get('order_datetime')
                
                matched_trade = {
                    'Trade Date': exit_dt.strftime('%Y-%m-%d') if exit_dt else '',
                    'Symbol': symbol,
                    'Side': 'Long',
                    'Entry Action': 'Buy',
                    'Exit Action': 'Sell',
                    'Entry Time': entry_dt.strftime('%H:%M:%S') if entry_dt else '',
                    'Exit Time': exit_dt.strftime('%H:%M:%S') if exit_dt else '',
                    'Entry Price': entry_price,
                    'Exit Price': exit_price,
                    'Quantity': quantity,
                    'PnL': round(pnl, 2),
                    'Result': result,
                    'Hold Time': calculate_hold_time(entry_dt, exit_dt) if entry_dt and exit_dt else ''
                }
                matched_trades.append(matched_trade)
    
    return matched_trades

def load_raw_imports() -> List[dict]:
    """Load all raw imports from CSV"""
    if not RAW_IMPORTS_FILE.exists():
        return []
    
    with open(RAW_IMPORTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_raw_imports(trades: List[dict]):
    """Save raw imports to CSV"""
    if not trades:
        return
    
    fieldnames = trades[0].keys()
    with open(RAW_IMPORTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)

def load_matched_trades() -> List[dict]:
    """Load matched trades from CSV"""
    if not TRADES_FILE.exists():
        return []
    
    with open(TRADES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_matched_trades(trades: List[dict]):
    """Save matched trades to CSV"""
    if not trades:
        return
    
    fieldnames = ['Trade Date', 'Symbol', 'Side', 'Entry Action', 'Exit Action',
                 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 'Quantity',
                 'PnL', 'Result', 'Hold Time']
    
    with open(TRADES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)

@api_router.post("/import", response_model=TradeImportResponse)
async def import_trades(file: UploadFile = File(...)):
    """Import trades from CSV file"""
    try:
        contents = await file.read()
        # Handle BOM and decode
        text = contents.decode('utf-8-sig')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(text))
        new_trades = []
        
        for row in csv_reader:
            status = row.get('Status', '')
            if 'Filled' in status and 'Verified Canceled' not in status:
                order_datetime = parse_fidelity_time(row.get('Order Time', ''))
                price = parse_price_from_status(status)
                
                if order_datetime and price:
                    trade = {
                        'Symbol': row.get('Symbol', ''),
                        'Action': row.get('Action', ''),
                        'Status': status,
                        'Amount': int(row.get('Amount', 0)),
                        'Order Time': row.get('Order Time', ''),
                        'order_datetime': order_datetime,
                        'price': price
                    }
                    new_trades.append(trade)
        
        # Load existing raw imports
        existing_trades = load_raw_imports()
        
        # Detect duplicates
        existing_keys = set()
        for t in existing_trades:
            key = f"{t.get('Symbol')}_{t.get('Action')}_{t.get('Order Time')}_{t.get('Amount')}"
            existing_keys.add(key)
        
        unique_new_trades = []
        duplicate_count = 0
        
        for trade in new_trades:
            key = f"{trade.get('Symbol')}_{trade.get('Action')}_{trade.get('Order Time')}_{trade.get('Amount')}"
            if key not in existing_keys:
                unique_new_trades.append(trade)
                existing_keys.add(key)
            else:
                duplicate_count += 1
        
        # Add unique trades to existing
        all_trades = existing_trades + unique_new_trades
        
        # Prepare for CSV storage (remove datetime objects)
        for trade in all_trades:
            if 'order_datetime' in trade and not isinstance(trade['order_datetime'], str):
                trade['order_datetime'] = trade['order_datetime'].isoformat()
        
        save_raw_imports(all_trades)
        
        # Re-parse for matching
        for trade in all_trades:
            if isinstance(trade.get('order_datetime'), str):
                try:
                    trade['order_datetime'] = datetime.fromisoformat(trade['order_datetime'])
                except:
                    # If parsing fails, try to parse as original format
                    try:
                        trade['order_datetime'] = parse_fidelity_time(trade.get('Order Time', ''))
                    except:
                        trade['order_datetime'] = None
        
        # Match all trades
        matched = match_trades(all_trades)
        save_matched_trades(matched)
        
        return TradeImportResponse(
            success=True,
            imported_count=len(unique_new_trades),
            duplicate_count=duplicate_count,
            matched_trades_count=len(matched),
            message=f"Imported {len(unique_new_trades)} new trades, {duplicate_count} duplicates skipped"
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/trades", response_model=List[MatchedTrade])
async def get_trades():
    """Get all matched trades"""
    trades = load_matched_trades()
    result = []
    
    for trade in trades:
        result.append(MatchedTrade(
            trade_date=trade.get('Trade Date', ''),
            symbol=trade.get('Symbol', ''),
            side=trade.get('Side', ''),
            entry_action=trade.get('Entry Action', ''),
            exit_action=trade.get('Exit Action', ''),
            entry_time=trade.get('Entry Time', ''),
            exit_time=trade.get('Exit Time', ''),
            entry_price=float(trade.get('Entry Price', 0)),
            exit_price=float(trade.get('Exit Price', 0)),
            quantity=int(trade.get('Quantity', 0)),
            pnl=float(trade.get('PnL', 0)),
            result=trade.get('Result', ''),
            hold_time=trade.get('Hold Time', '')
        ))
    
    return result

@api_router.get("/dashboard-metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Calculate and return dashboard metrics"""
    trades = load_matched_trades()
    
    if not trades:
        return DashboardMetrics(
            total_pnl=0, avg_daily_pnl=0, avg_trade_pnl=0,
            total_trades=0, winning_trades=0, losing_trades=0, scratch_trades=0,
            win_rate=0, loss_rate=0, scratch_rate=0,
            avg_winning_trade=0, avg_losing_trade=0,
            largest_gain=0, largest_loss=0,
            max_consecutive_wins=0, max_consecutive_losses=0,
            avg_hold_time_winning="00:00:00",
            avg_hold_time_losing="00:00:00",
            avg_hold_time_scratch="00:00:00"
        )
    
    # Calculate metrics
    total_pnl = sum(float(t.get('PnL', 0)) for t in trades)
    total_trades = len(trades)
    
    winning = [t for t in trades if t.get('Result') == 'Win']
    losing = [t for t in trades if t.get('Result') == 'Lose']
    scratch = [t for t in trades if t.get('Result') == 'Scratch']
    
    winning_trades = len(winning)
    losing_trades = len(losing)
    scratch_trades = len(scratch)
    
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    loss_rate = losing_trades / total_trades if total_trades > 0 else 0
    scratch_rate = scratch_trades / total_trades if total_trades > 0 else 0
    
    avg_winning_trade = sum(float(t.get('PnL', 0)) for t in winning) / winning_trades if winning_trades > 0 else 0
    avg_losing_trade = sum(float(t.get('PnL', 0)) for t in losing) / losing_trades if losing_trades > 0 else 0
    
    pnl_values = [float(t.get('PnL', 0)) for t in trades]
    largest_gain = max(pnl_values) if pnl_values else 0
    largest_loss = min(pnl_values) if pnl_values else 0
    
    # Calculate consecutive wins/losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0
    
    for trade in trades:
        result = trade.get('Result')
        if result == 'Win':
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        elif result == 'Lose':
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0
    
    # Calculate average hold times
    def avg_hold_time(trade_list):
        if not trade_list:
            return "00:00:00"
        
        total_seconds = 0
        for t in trade_list:
            hold_time = t.get('Hold Time', '00:00:00')
            parts = hold_time.split(':')
            if len(parts) == 3:
                total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        
        avg_seconds = total_seconds // len(trade_list) if trade_list else 0
        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60
        seconds = avg_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Calculate unique trading days
    unique_days = set(t.get('Trade Date') for t in trades if t.get('Trade Date'))
    avg_daily_pnl = total_pnl / len(unique_days) if unique_days else 0
    avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    return DashboardMetrics(
        total_pnl=round(total_pnl, 2),
        avg_daily_pnl=round(avg_daily_pnl, 2),
        avg_trade_pnl=round(avg_trade_pnl, 2),
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        scratch_trades=scratch_trades,
        win_rate=round(win_rate, 4),
        loss_rate=round(loss_rate, 4),
        scratch_rate=round(scratch_rate, 4),
        avg_winning_trade=round(avg_winning_trade, 2),
        avg_losing_trade=round(avg_losing_trade, 2),
        largest_gain=round(largest_gain, 2),
        largest_loss=round(largest_loss, 2),
        max_consecutive_wins=max_consecutive_wins,
        max_consecutive_losses=max_consecutive_losses,
        avg_hold_time_winning=avg_hold_time(winning),
        avg_hold_time_losing=avg_hold_time(losing),
        avg_hold_time_scratch=avg_hold_time(scratch)
    )

@api_router.get("/calendar-data", response_model=List[CalendarDay])
async def get_calendar_data():
    """Get daily P&L summary for calendar view"""
    trades = load_matched_trades()
    
    # Group by date
    daily_data = defaultdict(lambda: {'pnl': 0, 'count': 0})
    
    for trade in trades:
        date = trade.get('Trade Date')
        if date:
            daily_data[date]['pnl'] += float(trade.get('PnL', 0))
            daily_data[date]['count'] += 1
    
    result = [
        CalendarDay(
            date=date,
            pnl=round(data['pnl'], 2),
            trade_count=data['count']
        )
        for date, data in daily_data.items()
    ]
    
    return result

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
