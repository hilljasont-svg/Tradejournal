from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging
import csv
import io
from datetime import datetime, time
from collections import defaultdict
import re

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

class ColumnMapping(BaseModel):
    date: str
    symbol: str
    action: str
    price: str
    quantity: str
    time: Optional[str] = None
    date_time_combined: bool = False

class CSVPreview(BaseModel):
    headers: List[str]
    sample_rows: List[List[str]]
    suggested_mapping: Optional[Dict[str, str]]

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
    total_fees: float
    net_pnl: float
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
    fees: float
    net_pnl: float
    trade_count: int

class TimeAnalysis(BaseModel):
    hour: int
    trade_count: int
    total_pnl: float
    avg_pnl: float
    win_count: int
    loss_count: int
    win_rate: float

class SymbolPerformance(BaseModel):
    symbol: str
    trade_count: int
    total_pnl: float
    avg_pnl: float
    win_rate: float

class CumulativePnL(BaseModel):
    date: str
    pnl: float
    cumulative_pnl: float

def suggest_column_mapping(headers: List[str]) -> Dict[str, str]:
    """Auto-suggest column mapping based on header names"""
    mapping = {}
    headers_lower = [h.lower() for h in headers]
    
    # Date detection
    date_keywords = ['date', 'run date', 'trade date', 'order date']
    for keyword in date_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h:
                mapping['date'] = headers[i]
                break
        if 'date' in mapping:
            break
    
    # Symbol detection
    symbol_keywords = ['symbol', 'ticker', 'security']
    for keyword in symbol_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h:
                mapping['symbol'] = headers[i]
                break
        if 'symbol' in mapping:
            break
    
    # Action detection
    action_keywords = ['action', 'side', 'transaction', 'type']
    for keyword in action_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h and 'description' not in h:
                mapping['action'] = headers[i]
                break
        if 'action' in mapping:
            break
    
    # Price detection
    price_keywords = ['price', 'trade price', 'execution price', 'status']
    for keyword in price_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h:
                mapping['price'] = headers[i]
                break
        if 'price' in mapping:
            break
    
    # Quantity detection (prefer non-exchange quantity)
    quantity_keywords = ['quantity', 'qty', 'amount', 'shares']
    for keyword in quantity_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h and 'exchange' not in h and 'currency' not in h:
                mapping['quantity'] = headers[i]
                break
        if 'quantity' in mapping:
            break
    
    # If not found, check for quantity with exchange but prefer without
    if 'quantity' not in mapping:
        for i, h in enumerate(headers_lower):
            if 'quantity' in h:
                mapping['quantity'] = headers[i]
                break
    
    # Time detection (optional)
    time_keywords = ['time', 'order time', 'execution time']
    for keyword in time_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h:
                mapping['time'] = headers[i]
                break
    
    # Fees detection (optional)
    fees_keywords = ['fees', 'commission', 'charges']
    for keyword in fees_keywords:
        for i, h in enumerate(headers_lower):
            if keyword in h:
                mapping['fees'] = headers[i]
                break
    
    return mapping

def parse_flexible_date(date_str: str, has_time: bool = False) -> Optional[datetime]:
    """Parse various date formats"""
    if not date_str:
        return None
    
    formats = [
        "%b-%d-%Y %I:%M:%S %p",  # Dec-18-2025 3:31:36 PM
        "%m/%d/%Y %I:%M:%S %p",   # 12/18/2025 3:31:36 PM
        "%m/%d/%Y",               # 12/18/2025
        "%Y-%m-%d",               # 2025-12-18
        "%b %d, %Y",              # Dec 18, 2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    return None

def parse_flexible_time(time_str: str) -> Optional[datetime]:
    """Parse time with ET timezone notation"""
    try:
        # Handle "3:31:36 PM ET Dec-18-2025" format
        if ' ET ' in time_str:
            parts = time_str.split(' ET ')
            time_part = parts[0]
            date_part = parts[1]
            datetime_str = f"{date_part} {time_part}"
            return datetime.strptime(datetime_str, "%b-%d-%Y %I:%M:%S %p")
        else:
            return parse_flexible_date(time_str, True)
    except:
        return None

def extract_symbol(symbol_str: str) -> str:
    """Extract clean symbol from various formats"""
    if not symbol_str:
        return ""
    
    # Remove leading/trailing whitespace and special chars
    symbol = symbol_str.strip().lstrip('-').strip()
    
    # If it's already a clean option symbol like SPY251219P670, return as is
    if re.match(r'^[A-Z]+\d+[PC]\d+$', symbol):
        return symbol
    
    # Try to extract option symbol from description
    # Matches patterns like "SPY Dec 19 2025 670.00 Put" or "-SPY251219P670"
    match = re.search(r'([A-Z]+\d{6}[PC]\d+)', symbol)
    if match:
        return match.group(1)
    
    # If still contains description text, try to extract base symbol
    # e.g., "SPY Dec 19" -> look for the stock part
    parts = symbol.split()
    if parts:
        base = parts[0].strip('-')
        # Check if it's a valid ticker (2-5 uppercase letters)
        if re.match(r'^[A-Z]{2,5}$', base):
            return base
    
    return symbol

def determine_action(action_str: str, quantity: float) -> str:
    """Determine if it's a buy or sell action"""
    action_lower = action_str.lower()
    
    if 'buy' in action_lower or 'opening' in action_lower:
        return 'Buy'
    elif 'sell' in action_lower or 'closing' in action_lower:
        return 'Sell'
    elif quantity < 0:
        return 'Sell'
    else:
        return 'Buy'

def calculate_hold_time(entry_dt: datetime, exit_dt: datetime) -> str:
    """Calculate hold time in HH:MM:SS format"""
    diff = exit_dt - entry_dt
    total_seconds = int(diff.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def match_trades(raw_trades: List[dict]) -> List[dict]:
    """Match Buy and Sell trades with proper P&L calculation"""
    by_symbol = defaultdict(list)
    for idx, trade in enumerate(raw_trades):
        symbol = trade.get('Symbol', '').strip()
        if symbol:
            trade['_import_order'] = idx  # Preserve original order for ties
            by_symbol[symbol].append(trade)
    
    matched_trades = []
    
    for symbol, trades in by_symbol.items():
        # Sort by datetime, then by import order if datetime is same
        trades.sort(key=lambda t: (
            t.get('order_datetime', datetime.min),
            t.get('_import_order', 0)
        ))
        
        buy_queue = []
        sell_queue = []
        
        for trade in trades:
            action = trade.get('Action', '').upper()
            trade_value = abs(float(trade.get('trade_value', 0)))
            quantity = abs(int(trade.get('Amount', 0)))
            
            if 'BUY' in action or 'OPENING' in action:
                # Check if there are unmatched sells (short position)
                if sell_queue:
                    # This buy is closing a short position
                    while quantity > 0 and sell_queue:
                        sell_entry = sell_queue[0]
                        
                        if sell_entry['remaining_qty'] <= quantity:
                            matched_qty = sell_entry['remaining_qty']
                            this_match_cost = trade_value * (matched_qty / trade['Amount'])
                            this_match_revenue = sell_entry['revenue']
                            quantity -= matched_qty
                            sell_queue.pop(0)
                        else:
                            matched_qty = quantity
                            this_match_cost = trade_value * (matched_qty / trade['Amount'])
                            this_match_revenue = (sell_entry['revenue'] / sell_entry['quantity']) * matched_qty
                            sell_entry['remaining_qty'] -= matched_qty
                            quantity = 0
                        
                        # For shorts: P&L = revenue - cost (opposite of long)
                        pnl = this_match_revenue - this_match_cost
                        
                        if pnl > 5:
                            result = 'Win'
                        elif pnl < -5:
                            result = 'Lose'
                        else:
                            result = 'Scratch'
                        
                        entry_dt = sell_entry['datetime']
                        exit_dt = trade.get('order_datetime')
                        
                        # Calculate fees for this portion
                        entry_fees = sell_entry['trade'].get('fees', 0) * (matched_qty / sell_entry['quantity'])
                        exit_fees = trade.get('fees', 0) * (matched_qty / trade['Amount'])
                        total_fees = entry_fees + exit_fees
                        
                        matched_trade = {
                            'Trade Date': exit_dt.strftime('%Y-%m-%d') if exit_dt else '',
                            'Symbol': symbol,
                            'Side': 'Short',
                            'Entry Action': 'Sell',
                            'Exit Action': 'Buy',
                            'Entry Time': entry_dt.strftime('%H:%M:%S') if entry_dt else '00:00:00',
                            'Exit Time': exit_dt.strftime('%H:%M:%S') if exit_dt else '00:00:00',
                            'Entry Price': float(sell_entry['price']),
                            'Exit Price': float(trade.get('price', 0)),
                            'Quantity': int(matched_qty),
                            'PnL': round(pnl, 2),
                            'Fees': round(total_fees, 2),
                            'Result': result,
                            'Hold Time': calculate_hold_time(entry_dt, exit_dt) if entry_dt and exit_dt else '00:00:00',
                            'Entry Hour': entry_dt.hour if entry_dt else 0
                        }
                        matched_trades.append(matched_trade)
                
                # Add remaining to buy queue if any
                if quantity > 0:
                    buy_queue.append({
                        'datetime': trade.get('order_datetime'),
                        'price': trade.get('price', 0),
                        'quantity': quantity,
                        'remaining_qty': quantity,
                        'cost': trade_value * (quantity / trade['Amount']),
                        'trade': trade
                    })
            
            elif 'SELL' in action or 'CLOSING' in action:
                sell_value = trade_value
                sell_qty = quantity
                sell_dt = trade.get('order_datetime')
                sell_price = trade.get('price', 0)
                
                qty_to_match = sell_qty
                
                # Match with existing buy queue (closing long positions)
                while qty_to_match > 0 and buy_queue:
                    buy_entry = buy_queue[0]
                    
                    if buy_entry['remaining_qty'] <= qty_to_match:
                        matched_qty = buy_entry['remaining_qty']
                        this_match_cost = (buy_entry['cost'] / buy_entry['quantity']) * matched_qty
                        qty_to_match -= matched_qty
                        buy_queue.pop(0)
                    else:
                        matched_qty = qty_to_match
                        this_match_cost = (buy_entry['cost'] / buy_entry['quantity']) * matched_qty
                        buy_entry['remaining_qty'] -= matched_qty
                        qty_to_match = 0
                    
                    pnl = sell_value * (matched_qty / sell_qty) - this_match_cost
                    
                    logging.info(f"Match: {symbol} qty={matched_qty}, sell_val={sell_value}, sell_qty={sell_qty}, cost={this_match_cost}, pnl={pnl}")
                    
                    if pnl > 5:
                        result = 'Win'
                    elif pnl < -5:
                        result = 'Lose'
                    else:
                        result = 'Scratch'
                    
                    entry_dt = buy_entry['datetime']
                    
                    # Calculate fees for this portion
                    entry_fees = buy_entry['trade'].get('fees', 0) * (matched_qty / buy_entry['quantity'])
                    exit_fees = trade.get('fees', 0) * (matched_qty / sell_qty)
                    total_fees = entry_fees + exit_fees
                    
                    matched_trade = {
                        'Trade Date': sell_dt.strftime('%Y-%m-%d') if sell_dt else '',
                        'Symbol': symbol,
                        'Side': 'Long',
                        'Entry Action': 'Buy',
                        'Exit Action': 'Sell',
                        'Entry Time': entry_dt.strftime('%H:%M:%S') if entry_dt else '00:00:00',
                        'Exit Time': sell_dt.strftime('%H:%M:%S') if sell_dt else '00:00:00',
                        'Entry Price': float(buy_entry['price']),
                        'Exit Price': float(sell_price),
                        'Quantity': int(matched_qty),
                        'PnL': round(pnl, 2),
                        'Fees': round(total_fees, 2),
                        'Result': result,
                        'Hold Time': calculate_hold_time(entry_dt, sell_dt) if entry_dt and sell_dt else '00:00:00',
                        'Entry Hour': entry_dt.hour if entry_dt else 0
                    }
                    matched_trades.append(matched_trade)
                
                # Add unmatched sell quantity to sell queue (opening short position)
                if qty_to_match > 0:
                    sell_queue.append({
                        'datetime': sell_dt,
                        'price': sell_price,
                        'quantity': qty_to_match,
                        'remaining_qty': qty_to_match,
                        'revenue': sell_value * (qty_to_match / sell_qty),
                        'trade': trade
                    })
    
    return matched_trades

def load_raw_imports() -> List[dict]:
    if not RAW_IMPORTS_FILE.exists():
        return []
    
    with open(RAW_IMPORTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_raw_imports(trades: List[dict]):
    if not trades:
        return
    
    fieldnames = trades[0].keys()
    with open(RAW_IMPORTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)

def load_matched_trades() -> List[dict]:
    if not TRADES_FILE.exists():
        return []
    
    with open(TRADES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_matched_trades(trades: List[dict]):
    if not trades:
        return
    
    fieldnames = ['Trade Date', 'Symbol', 'Side', 'Entry Action', 'Exit Action',
                 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 'Quantity',
                 'PnL', 'Fees', 'Result', 'Hold Time', 'Entry Hour']
    
    with open(TRADES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)

@api_router.post("/preview-csv")
async def preview_csv(file: UploadFile = File(...)):
    """Preview CSV and suggest column mapping"""
    try:
        contents = await file.read()
        text = contents.decode('utf-8-sig')
        
        # Remove empty lines
        lines = [line for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        csv_reader = csv.DictReader(io.StringIO(text))
        headers = csv_reader.fieldnames
        
        sample_rows = []
        for i, row in enumerate(csv_reader):
            if i >= 5:
                break
            sample_rows.append([row.get(h, '') for h in headers])
        
        suggested_mapping = suggest_column_mapping(headers)
        
        return {
            "headers": headers,
            "sample_rows": sample_rows,
            "suggested_mapping": suggested_mapping
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/import-with-mapping", response_model=TradeImportResponse)
async def import_with_mapping(
    file: UploadFile = File(...),
    mapping: str = Form(None)
):
    """Import trades with custom column mapping"""
    try:
        import json
        logging.info(f"Received mapping param: {mapping}")
        column_mapping = json.loads(mapping) if mapping else {}
        logging.info(f"Parsed column_mapping: {column_mapping}")
        
        contents = await file.read()
        text = contents.decode('utf-8-sig')
        
        # Remove empty lines
        lines = [line for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        csv_reader = csv.DictReader(io.StringIO(text))
        new_trades = []
        
        row_count = 0
        for row in csv_reader:
            row_count += 1
            try:
                logging.info(f"Processing row {row_count}")
                # Extract mapped columns
                date_col = column_mapping.get('date')
                symbol_col = column_mapping.get('symbol')
                action_col = column_mapping.get('action')
                price_col = column_mapping.get('price')
                quantity_col = column_mapping.get('quantity')
                time_col = column_mapping.get('time')
                date_time_combined = column_mapping.get('date_time_combined', False)
                
                logging.info(f"Column mapping - date:{date_col}, symbol:{symbol_col}, price:{price_col}, qty:{quantity_col}")
                
                if not all([date_col, symbol_col, price_col, quantity_col]):
                    logging.warning(f"Missing required columns - skipping row")
                    continue
                
                # Parse date/time
                if date_time_combined and time_col:
                    order_datetime = parse_flexible_time(row.get(time_col, ''))
                elif time_col:
                    date_str = row.get(date_col, '')
                    time_str = row.get(time_col, '')
                    combined = f"{date_str} {time_str}"
                    order_datetime = parse_flexible_date(combined, True)
                else:
                    order_datetime = parse_flexible_date(row.get(date_col, ''))
                
                if not order_datetime:
                    order_datetime = datetime.now()
                
                # Extract and clean data
                symbol = extract_symbol(row.get(symbol_col, ''))
                
                # Parse price (handle "Filled at $X.XX" format)
                price_raw = str(row.get(price_col, '0'))
                price = 0
                if 'Filled at' in price_raw or 'filled at' in price_raw:
                    # Extract price from "Filled at $X.XX" format
                    try:
                        price_str = price_raw.split('at')[1].replace('$', '').replace(',', '').strip().split()[0]
                        price = float(price_str)
                    except:
                        price = 0
                else:
                    # Direct price value
                    try:
                        price = float(price_raw.replace(',', '').replace('$', '').strip())
                    except:
                        price = 0
                
                quantity_raw = str(row.get(quantity_col, '0')).replace(',', '').strip()
                # Handle empty or invalid quantity
                try:
                    quantity_val = float(quantity_raw) if quantity_raw and quantity_raw not in ['', '0'] else 0
                    quantity = abs(quantity_val)
                except (ValueError, TypeError):
                    quantity = 0
                    quantity_val = 0
                
                # Determine action
                if action_col and action_col != 'none':
                    action = determine_action(row.get(action_col, ''), quantity_val)
                else:
                    action = 'Buy' if quantity_val >= 0 else 'Sell'
                
                # Debug logging
                logging.info(f'Processed row - Symbol: \'{symbol}\', Price: {price}, Quantity: {quantity}, Action: {action}')
                
                # Check if options (must have date + P/C + strike pattern)
                # Options format: SYMBOL + YYMMDD + P/C + STRIKE (e.g., SPY251218P672)
                is_option = bool(re.search(r'[A-Z]+\d{6}[PC]\d+', symbol))
                multiplier = 100 if is_option else 1
                trade_value = price * quantity * multiplier
                
                # Extract fees if available
                fees_col = column_mapping.get('fees')
                fees = 0
                if fees_col:
                    try:
                        fees = abs(float(row.get(fees_col, 0)))
                    except:
                        fees = 0
                
                logging.info(f"Symbol: {symbol}, is_option: {is_option}, multiplier: {multiplier}")
                
                if symbol and price > 0 and quantity > 0:
                    trade = {
                        'Symbol': symbol,
                        'Action': action,
                        'Status': 'Filled',
                        'Amount': int(quantity),
                        'Order Time': order_datetime.strftime('%I:%M:%S %p ET %b-%d-%Y'),
                        'order_datetime': order_datetime,
                        'price': price,
                        'trade_value': trade_value,
                        'fees': fees
                    }
                    new_trades.append(trade)
                    logging.info("Trade added: %s @ %s x %s (value: %s, fees: %s)", symbol, price, quantity, trade_value, fees)
                else:
                    logging.warning("Trade rejected - Symbol: '%s' (valid:%s), Price: %s (>0:%s), Qty: %s (>0:%s)", symbol, bool(symbol), price, price > 0, quantity, quantity > 0)
            except Exception as e:
                logging.error(f"Error processing row: {e}")
                continue
        
        existing_trades = load_raw_imports()
        
        existing_keys = set()
        for t in existing_trades:
            key = f"{t.get('Symbol')}_{t.get('Action')}_{t.get('Amount')}_{t.get('price')}"
            existing_keys.add(key)
        
        unique_new_trades = []
        duplicate_count = 0
        
        for trade in new_trades:
            key = f"{trade.get('Symbol')}_{trade.get('Action')}_{trade.get('Amount')}_{trade.get('price')}"
            if key not in existing_keys:
                unique_new_trades.append(trade)
                existing_keys.add(key)
            else:
                duplicate_count += 1
        
        all_trades = existing_trades + unique_new_trades
        
        for trade in all_trades:
            if 'order_datetime' in trade and not isinstance(trade['order_datetime'], str):
                trade['order_datetime'] = trade['order_datetime'].isoformat()
        
        save_raw_imports(all_trades)
        
        for trade in all_trades:
            if isinstance(trade.get('order_datetime'), str):
                trade['order_datetime'] = datetime.fromisoformat(trade['order_datetime'])
        
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
        logging.error(f"Import error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/trades", response_model=List[MatchedTrade])
async def get_trades(start_date: str = None, end_date: str = None):
    trades = load_matched_trades()
    
    # Filter by date range
    if start_date or end_date:
        filtered = []
        for trade in trades:
            trade_date = trade.get('Trade Date', '')
            if start_date and trade_date < start_date:
                continue
            if end_date and trade_date > end_date:
                continue
            filtered.append(trade)
        trades = filtered
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
async def get_dashboard_metrics(start_date: str = None, end_date: str = None):
    trades = load_matched_trades()
    
    # Filter by date range
    if start_date or end_date:
        filtered = []
        for trade in trades:
            trade_date = trade.get('Trade Date', '')
            if start_date and trade_date < start_date:
                continue
            if end_date and trade_date > end_date:
                continue
            filtered.append(trade)
        trades = filtered
    
    if not trades:
        return DashboardMetrics(
            total_pnl=0, total_fees=0, net_pnl=0, avg_daily_pnl=0, avg_trade_pnl=0,
            total_trades=0, winning_trades=0, losing_trades=0, scratch_trades=0,
            win_rate=0, loss_rate=0, scratch_rate=0,
            avg_winning_trade=0, avg_losing_trade=0,
            largest_gain=0, largest_loss=0,
            max_consecutive_wins=0, max_consecutive_losses=0,
            avg_hold_time_winning="00:00:00",
            avg_hold_time_losing="00:00:00",
            avg_hold_time_scratch="00:00:00"
        )
    
    total_pnl = sum(float(t.get('PnL', 0)) for t in trades)
    total_fees = sum(float(t.get('Fees', 0)) for t in trades)
    net_pnl = total_pnl - total_fees
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
    
    def avg_hold_time(trade_list):
        if not trade_list:
            return "00:00:00"
        
        total_seconds = 0
        for t in trade_list:
            hold_time = t.get('Hold Time', '00:00:00')
            parts = hold_time.split(':')
            if len(parts) == 3:
                try:
                    total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                except:
                    pass
        
        avg_seconds = total_seconds // len(trade_list) if trade_list else 0
        hours = avg_seconds // 3600
        minutes = (avg_seconds % 3600) // 60
        seconds = avg_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    unique_days = set(t.get('Trade Date') for t in trades if t.get('Trade Date'))
    avg_daily_pnl = total_pnl / len(unique_days) if unique_days else 0
    avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    return DashboardMetrics(
        total_pnl=round(total_pnl, 2),
        total_fees=round(total_fees, 2),
        net_pnl=round(net_pnl, 2),
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
async def get_calendar_data(start_date: str = None, end_date: str = None):
    trades = load_matched_trades()
    
    # Filter by date range
    if start_date or end_date:
        filtered = []
        for trade in trades:
            trade_date = trade.get('Trade Date', '')
            if start_date and trade_date < start_date:
                continue
            if end_date and trade_date > end_date:
                continue
            filtered.append(trade)
        trades = filtered
    
    daily_data = defaultdict(lambda: {'pnl': 0, 'fees': 0, 'count': 0})
    
    for trade in trades:
        date = trade.get('Trade Date')
        if date:
            daily_data[date]['pnl'] += float(trade.get('PnL', 0))
            daily_data[date]['fees'] += float(trade.get('Fees', 0))
            daily_data[date]['count'] += 1
    
    result = [
        CalendarDay(
            date=date,
            pnl=round(data['pnl'], 2),
            fees=round(data['fees'], 2),
            net_pnl=round(data['pnl'] - data['fees'], 2),
            trade_count=data['count']
        )
        for date, data in daily_data.items()
    ]
    
    return result

@api_router.get("/time-analysis", response_model=List[TimeAnalysis])
async def get_time_analysis():
    trades = load_matched_trades()
    
    hourly_data = defaultdict(lambda: {'trades': [], 'wins': 0, 'losses': 0})
    
    for trade in trades:
        entry_time = trade.get('Entry Time', '')
        if entry_time:
            try:
                hour = int(entry_time.split(':')[0])
                pnl = float(trade.get('PnL', 0))
                hourly_data[hour]['trades'].append(pnl)
                if trade.get('Result') == 'Win':
                    hourly_data[hour]['wins'] += 1
                elif trade.get('Result') == 'Lose':
                    hourly_data[hour]['losses'] += 1
            except:
                pass
    
    result = []
    for hour in range(24):
        if hour in hourly_data:
            data = hourly_data[hour]
            trade_count = len(data['trades'])
            total_pnl = sum(data['trades'])
            avg_pnl = total_pnl / trade_count if trade_count > 0 else 0
            win_rate = data['wins'] / trade_count if trade_count > 0 else 0
            
            result.append(TimeAnalysis(
                hour=hour,
                trade_count=trade_count,
                total_pnl=round(total_pnl, 2),
                avg_pnl=round(avg_pnl, 2),
                win_count=data['wins'],
                loss_count=data['losses'],
                win_rate=round(win_rate, 4)
            ))
    
    return result

@api_router.get("/symbol-performance", response_model=List[SymbolPerformance])
async def get_symbol_performance():
    trades = load_matched_trades()
    
    symbol_data = defaultdict(lambda: {'pnls': [], 'wins': 0})
    
    for trade in trades:
        symbol = trade.get('Symbol', '')
        if symbol:
            pnl = float(trade.get('PnL', 0))
            symbol_data[symbol]['pnls'].append(pnl)
            if trade.get('Result') == 'Win':
                symbol_data[symbol]['wins'] += 1
    
    result = []
    for symbol, data in symbol_data.items():
        trade_count = len(data['pnls'])
        total_pnl = sum(data['pnls'])
        avg_pnl = total_pnl / trade_count if trade_count > 0 else 0
        win_rate = data['wins'] / trade_count if trade_count > 0 else 0
        
        result.append(SymbolPerformance(
            symbol=symbol,
            trade_count=trade_count,
            total_pnl=round(total_pnl, 2),
            avg_pnl=round(avg_pnl, 2),
            win_rate=round(win_rate, 4)
        ))
    
    result.sort(key=lambda x: x.total_pnl, reverse=True)
    
    return result

@api_router.get("/cumulative-pnl", response_model=List[CumulativePnL])
async def get_cumulative_pnl():
    trades = load_matched_trades()
    
    sorted_trades = sorted(trades, key=lambda t: f"{t.get('Trade Date', '')} {t.get('Exit Time', '')}")
    
    cumulative = 0
    result = []
    
    for trade in sorted_trades:
        date = trade.get('Trade Date', '')
        pnl = float(trade.get('PnL', 0))
        cumulative += pnl
        
        result.append(CumulativePnL(
            date=f"{date} {trade.get('Exit Time', '')}",
            pnl=round(pnl, 2),
            cumulative_pnl=round(cumulative, 2)
        ))
    
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
