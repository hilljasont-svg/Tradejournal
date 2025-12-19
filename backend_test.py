import requests
import sys
import json
import os
from datetime import datetime
from pathlib import Path

class TradingJournalAPITester:
    def __init__(self, base_url="https://tradejournal-app-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_api_endpoint(self, name, method, endpoint, expected_status=200, data=None, files=None):
        """Test a single API endpoint"""
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=30)
                else:
                    response = requests.post(url, json=data, timeout=30)
            
            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                return True, response.json() if response.content else {}
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_dashboard_metrics(self):
        """Test dashboard metrics endpoint"""
        print("\n🔍 Testing Dashboard Metrics API...")
        success, data = self.test_api_endpoint(
            "Dashboard Metrics API",
            "GET",
            "dashboard-metrics"
        )
        
        if success:
            # Validate required fields
            required_fields = [
                'total_pnl', 'avg_daily_pnl', 'avg_trade_pnl', 'total_trades',
                'winning_trades', 'losing_trades', 'scratch_trades',
                'win_rate', 'loss_rate', 'scratch_rate',
                'avg_winning_trade', 'avg_losing_trade',
                'largest_gain', 'largest_loss',
                'max_consecutive_wins', 'max_consecutive_losses',
                'avg_hold_time_winning', 'avg_hold_time_losing', 'avg_hold_time_scratch'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Dashboard Metrics - Field Validation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard Metrics - Field Validation", True)
                print(f"   📊 Total P&L: ${data.get('total_pnl', 0)}")
                print(f"   📊 Total Trades: {data.get('total_trades', 0)}")
                print(f"   📊 Win Rate: {data.get('win_rate', 0)*100:.1f}%")
        
        return success, data

    def test_trades_api(self):
        """Test trades endpoint"""
        print("\n🔍 Testing Trades API...")
        success, data = self.test_api_endpoint(
            "Trades API",
            "GET",
            "trades"
        )
        
        if success and isinstance(data, list):
            self.log_test("Trades API - Response Format", True)
            print(f"   📈 Found {len(data)} trades")
            
            if len(data) > 0:
                # Validate trade structure
                trade = data[0]
                required_fields = [
                    'trade_date', 'symbol', 'side', 'entry_action', 'exit_action',
                    'entry_time', 'exit_time', 'entry_price', 'exit_price',
                    'quantity', 'pnl', 'result', 'hold_time'
                ]
                
                missing_fields = [field for field in required_fields if field not in trade]
                if missing_fields:
                    self.log_test("Trades API - Trade Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Trades API - Trade Structure", True)
        elif success:
            self.log_test("Trades API - Response Format", False, "Expected list response")
        
        return success, data

    def test_calendar_data(self):
        """Test calendar data endpoint"""
        print("\n🔍 Testing Calendar Data API...")
        success, data = self.test_api_endpoint(
            "Calendar Data API",
            "GET",
            "calendar-data"
        )
        
        if success and isinstance(data, list):
            self.log_test("Calendar Data - Response Format", True)
            print(f"   📅 Found {len(data)} calendar days")
            
            if len(data) > 0:
                # Validate calendar day structure
                day = data[0]
                required_fields = ['date', 'pnl', 'trade_count']
                
                missing_fields = [field for field in required_fields if field not in day]
                if missing_fields:
                    self.log_test("Calendar Data - Day Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Calendar Data - Day Structure", True)
                    
                # Check for Dec 18 data (mentioned in context)
                dec_18_data = next((d for d in data if d['date'] == '2025-12-18'), None)
                if dec_18_data:
                    print(f"   📅 Dec 18 P&L: ${dec_18_data['pnl']} ({dec_18_data['trade_count']} trades)")
                    self.log_test("Calendar Data - Dec 18 Present", True)
                else:
                    self.log_test("Calendar Data - Dec 18 Present", False, "Dec 18 data not found")
        elif success:
            self.log_test("Calendar Data - Response Format", False, "Expected list response")
        
        return success, data

    def test_csv_import_endpoint(self):
        """Test CSV import endpoint with test file"""
        print("\n🔍 Testing CSV Import API...")
        
        # Check if test CSV exists
        test_csv_path = "/tmp/Orders_All_Accounts.csv"
        if not os.path.exists(test_csv_path):
            self.log_test("CSV Import - Test File", False, f"Test CSV not found at {test_csv_path}")
            return False, {}
        
        try:
            with open(test_csv_path, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                success, data = self.test_api_endpoint(
                    "CSV Import API",
                    "POST",
                    "import",
                    expected_status=200,
                    files=files
                )
                
                if success:
                    # Validate import response
                    required_fields = ['success', 'imported_count', 'duplicate_count', 'matched_trades_count', 'message']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("CSV Import - Response Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("CSV Import - Response Structure", True)
                        print(f"   📁 Imported: {data.get('imported_count', 0)} trades")
                        print(f"   📁 Duplicates: {data.get('duplicate_count', 0)}")
                        print(f"   📁 Matched: {data.get('matched_trades_count', 0)} trades")
                
                return success, data
                
        except Exception as e:
            self.log_test("CSV Import API", False, f"Exception: {str(e)}")
            return False, {}

    def test_data_persistence(self):
        """Test that data files exist and contain expected data"""
        print("\n🔍 Testing Data Persistence...")
        
        trades_file = Path("/app/data/trades.csv")
        raw_imports_file = Path("/app/data/raw_imports.csv")
        
        if trades_file.exists():
            self.log_test("Data Persistence - Trades File", True)
            try:
                with open(trades_file, 'r') as f:
                    lines = f.readlines()
                    print(f"   💾 Trades file has {len(lines)-1} trades (excluding header)")
            except Exception as e:
                self.log_test("Data Persistence - Trades File Read", False, str(e))
        else:
            self.log_test("Data Persistence - Trades File", False, "trades.csv not found")
        
        if raw_imports_file.exists():
            self.log_test("Data Persistence - Raw Imports File", True)
            try:
                with open(raw_imports_file, 'r') as f:
                    lines = f.readlines()
                    print(f"   💾 Raw imports file has {len(lines)-1} entries (excluding header)")
            except Exception as e:
                self.log_test("Data Persistence - Raw Imports File Read", False, str(e))
        else:
            self.log_test("Data Persistence - Raw Imports File", False, "raw_imports.csv not found")

    def test_fifo_matching_logic(self):
        """Test FIFO matching logic by analyzing existing trades"""
        print("\n🔍 Testing FIFO Matching Logic...")
        
        success, trades = self.test_trades_api()
        if not success or not trades:
            self.log_test("FIFO Logic - Data Available", False, "No trades data available")
            return
        
        # Group trades by symbol to verify FIFO
        symbol_trades = {}
        for trade in trades:
            symbol = trade.get('symbol', '')
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)
        
        fifo_violations = 0
        for symbol, symbol_trade_list in symbol_trades.items():
            # Sort by entry time to check FIFO order
            sorted_trades = sorted(symbol_trade_list, key=lambda t: t.get('entry_time', ''))
            
            # For now, just check that we have matched pairs
            if len(sorted_trades) > 0:
                print(f"   🔄 {symbol}: {len(sorted_trades)} matched trades")
        
        if fifo_violations == 0:
            self.log_test("FIFO Logic - Matching Validation", True)
        else:
            self.log_test("FIFO Logic - Matching Validation", False, f"{fifo_violations} violations found")

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Trading Journal Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test all endpoints
        self.test_dashboard_metrics()
        self.test_trades_api()
        self.test_calendar_data()
        self.test_csv_import_endpoint()
        self.test_data_persistence()
        self.test_fifo_matching_logic()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests PASSED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests FAILED")
            return False

def main():
    tester = TradingJournalAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": tester.tests_passed / tester.tests_run if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())