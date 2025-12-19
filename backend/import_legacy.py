"""Legacy import for Orders_All_Accounts.csv format"""
import csv
import io
from datetime import datetime
import re

def parse_fidelity_orders_format(text: str):
    """Parse the original Fidelity Orders format"""
    # Remove BOM and empty lines
    lines = [line for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    csv_reader = csv.DictReader(io.StringIO(text))
    trades = []
    
    for row in csv_reader:
        status = row.get('Status', '')
        if 'Filled' in status and 'Verified Canceled' not in status:
            # Parse time
            order_time_str = row.get('Order Time', '')
            try:
                parts = order_time_str.split(' ET ')
                if len(parts) == 2:
                    time_part = parts[0]
                    date_part = parts[1]
                    datetime_str = f"{date_part} {time_part}"
                    order_datetime = datetime.strptime(datetime_str, "%b-%d-%Y %I:%M:%S %p")
                else:
                    continue
            except:
                continue
            
            # Parse price from status
            price = None
            if 'Filled at $' in status:
                try:
                    price_str = status.split('Filled at $')[1].split(',')[0].strip()
                    price = float(price_str)
                except:
                    continue
            
            if not price:
                continue
            
            symbol = row.get('Symbol', '').strip()
            action = row.get('Action', '')
            quantity = int(row.get('Amount', 0))
            
            # Check if options
            is_option = bool(re.search(r'[PC]\d+$', symbol))
            multiplier = 100 if is_option else 1
            trade_value = price * abs(quantity) * multiplier
            
            if symbol and quantity != 0:
                trade = {
                    'Symbol': symbol,
                    'Action': action,
                    'Status': status,
                    'Amount': abs(quantity),
                    'Order Time': order_time_str,
                    'order_datetime': order_datetime,
                    'price': price,
                    'trade_value': trade_value
                }
                trades.append(trade)
    
    return trades
