import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, TrendingUp, TrendingDown, Calendar as CalendarIcon, BarChart3, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import MetricsGrid from '../components/MetricsGrid';
import CalendarView from '../components/CalendarView';
import TradeList from '../components/TradeList';
import ReportsView from '../components/ReportsView';
import ImportDialog from '../components/ImportDialog';
import { formatCurrency } from '../utils/formatters';
import { Toaster, toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [trades, setTrades] = useState([]);
  const [calendarData, setCalendarData] = useState([]);
  const [showImport, setShowImport] = useState(false);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('dashboard');
  
  // Date filter
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [showDatePicker, setShowDatePicker] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const params = {};
      if (startDate) params.start_date = startDate.toISOString().split('T')[0];
      if (endDate) params.end_date = endDate.toISOString().split('T')[0];
      
      const [metricsRes, tradesRes, calendarRes] = await Promise.all([
        axios.get(`${API}/dashboard-metrics`, { params }),
        axios.get(`${API}/trades`, { params }),
        axios.get(`${API}/calendar-data`, { params })
      ]);
      
      setMetrics(metricsRes.data);
      setTrades(tradesRes.data);
      setCalendarData(calendarRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  const handleImportSuccess = () => {
    setShowImport(false);
    fetchData();
    toast.success('Trades imported successfully!');
  };

  const setPreset = (preset) => {
    const now = new Date();
    let start;
    
    switch(preset) {
      case 'today':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        setStartDate(start);
        setEndDate(now);
        break;
      case 'week':
        start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        setStartDate(start);
        setEndDate(now);
        break;
      case 'month':
        start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        setStartDate(start);
        setEndDate(now);
        break;
      case 'year':
        start = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        setStartDate(start);
        setEndDate(now);
        break;
      case 'all':
        setStartDate(null);
        setEndDate(null);
        break;
    }
    setShowDatePicker(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="text-[#FAFAFA] font-['JetBrains_Mono'] text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090B] text-[#FAFAFA] p-6 md:p-8" data-testid="dashboard-container">
      <Toaster position="top-right" theme="dark" />
      
      <div className="max-w-[1600px] mx-auto mb-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold font-['JetBrains_Mono'] tracking-tight mb-2" data-testid="dashboard-title">
              Trading Journal
            </h1>
            <p className="text-[#A1A1AA] text-sm">
              Track, analyze, and improve your trading performance
            </p>
          </div>
          <div className="flex gap-3">
            <div className="relative">
              <Button
                onClick={() => setShowDatePicker(!showDatePicker)}
                variant="outline"
                className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA] hover:bg-[#3F3F46] rounded-sm font-['JetBrains_Mono']"
                data-testid="filter-button"
              >
                <Filter className="mr-2 h-4 w-4" />
                {startDate || endDate ? 'Filtered' : 'Filter'}
              </Button>
              
              {showDatePicker && (
                <div className="absolute right-0 mt-2 p-4 bg-[#18181B] border border-[#27272A] rounded-sm shadow-lg z-50" style={{width: '320px'}}>
                  <div className="space-y-3">
                    <div className="flex gap-2 flex-wrap">
                      <button onClick={() => setPreset('today')} className="px-3 py-1 text-xs bg-[#27272A] hover:bg-[#3F3F46] rounded-sm">Today</button>
                      <button onClick={() => setPreset('week')} className="px-3 py-1 text-xs bg-[#27272A] hover:bg-[#3F3F46] rounded-sm">Week</button>
                      <button onClick={() => setPreset('month')} className="px-3 py-1 text-xs bg-[#27272A] hover:bg-[#3F3F46] rounded-sm">Month</button>
                      <button onClick={() => setPreset('year')} className="px-3 py-1 text-xs bg-[#27272A] hover:bg-[#3F3F46] rounded-sm">Year</button>
                      <button onClick={() => setPreset('all')} className="px-3 py-1 text-xs bg-[#27272A] hover:bg-[#3F3F46] rounded-sm">All</button>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs text-[#A1A1AA]">Start Date</label>
                      <DatePicker
                        selected={startDate}
                        onChange={(date) => setStartDate(date)}
                        className="w-full bg-[#27272A] border border-[#3F3F46] rounded-sm p-2 text-sm"
                        dateFormat="MM/dd/yyyy"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs text-[#A1A1AA]">End Date</label>
                      <DatePicker
                        selected={endDate}
                        onChange={(date) => setEndDate(date)}
                        className="w-full bg-[#27272A] border border-[#3F3F46] rounded-sm p-2 text-sm"
                        dateFormat="MM/dd/yyyy"
                      />
                    </div>
                    <Button
                      onClick={() => setShowDatePicker(false)}
                      className="w-full bg-[#FAFAFA] text-[#18181B] hover:bg-[#E4E4E7] rounded-sm"
                    >
                      Apply
                    </Button>
                  </div>
                </div>
              )}
            </div>
            
            <Button
              onClick={() => setShowImport(true)}
              className="bg-[#FAFAFA] text-[#18181B] hover:bg-[#E4E4E7] rounded-sm font-['JetBrains_Mono'] font-medium"
              data-testid="import-button"
            >
              <Upload className="mr-2 h-4 w-4" />
              Import CSV
            </Button>
          </div>
        </div>

        <div className="flex gap-2 mb-6 border-b border-[#27272A]">
          <button
            onClick={() => setView('dashboard')}
            className={`px-4 py-2 font-['JetBrains_Mono'] text-sm font-medium transition-colors ${
              view === 'dashboard'
                ? 'text-[#FAFAFA] border-b-2 border-[#FAFAFA]'
                : 'text-[#A1A1AA] hover:text-[#FAFAFA]'
            }`}
            data-testid="tab-dashboard"
          >
            Dashboard
          </button>
          <button
            onClick={() => setView('reports')}
            className={`px-4 py-2 font-['JetBrains_Mono'] text-sm font-medium transition-colors ${
              view === 'reports'
                ? 'text-[#FAFAFA] border-b-2 border-[#FAFAFA]'
                : 'text-[#A1A1AA] hover:text-[#FAFAFA]'
            }`}
            data-testid="tab-reports"
          >
            <BarChart3 className="inline mr-2 h-4 w-4" />
            Reports
          </button>
          <button
            onClick={() => setView('calendar')}
            className={`px-4 py-2 font-['JetBrains_Mono'] text-sm font-medium transition-colors ${
              view === 'calendar'
                ? 'text-[#FAFAFA] border-b-2 border-[#FAFAFA]'
                : 'text-[#A1A1AA] hover:text-[#FAFAFA]'
            }`}
            data-testid="tab-calendar"
          >
            <CalendarIcon className="inline mr-2 h-4 w-4" />
            Calendar
          </button>
          <button
            onClick={() => setView('trades')}
            className={`px-4 py-2 font-['JetBrains_Mono'] text-sm font-medium transition-colors ${
              view === 'trades'
                ? 'text-[#FAFAFA] border-b-2 border-[#FAFAFA]'
                : 'text-[#A1A1AA] hover:text-[#FAFAFA]'
            }`}
            data-testid="tab-trades"
          >
            Trades Journal
          </button>
        </div>

        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[#A1A1AA] text-sm mb-1 font-['Inter']">Trade P&L</p>
                  <p
                    className={`text-3xl font-bold font-['JetBrains_Mono'] ${
                      metrics.total_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                    }`}
                    data-testid="total-pnl"
                  >
                    {formatCurrency(metrics.total_pnl)}
                  </p>
                </div>
                {metrics.total_pnl >= 0 ? (
                  <TrendingUp className="h-8 w-8 text-[#10B981]" />
                ) : (
                  <TrendingDown className="h-8 w-8 text-[#EF4444]" />
                )}
              </div>
            </Card>

            <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
              <p className="text-[#A1A1AA] text-sm mb-1 font-['Inter']">Win Rate</p>
              <p className="text-3xl font-bold font-['JetBrains_Mono'] text-[#FAFAFA]" data-testid="win-rate">
                {(metrics.win_rate * 100).toFixed(1)}%
              </p>
              <p className="text-[#71717A] text-xs mt-2 font-['Inter']">
                {metrics.winning_trades} wins / {metrics.total_trades} trades
              </p>
            </Card>

            <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
              <p className="text-[#A1A1AA] text-sm mb-1 font-['Inter']">Commissions</p>
              <p className="text-3xl font-bold font-['JetBrains_Mono'] text-[#EF4444]" data-testid="total-commissions">
                -{formatCurrency(metrics.total_fees)}
              </p>
            </Card>

            <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[#A1A1AA] text-sm mb-1 font-['Inter']">Net P&L</p>
                  <p
                    className={`text-3xl font-bold font-['JetBrains_Mono'] ${
                      metrics.net_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                    }`}
                    data-testid="net-pnl"
                  >
                    {formatCurrency(metrics.net_pnl)}
                  </p>
                  <p className="text-[#71717A] text-xs mt-2 font-['Inter']">After commissions</p>
                </div>
                {metrics.net_pnl >= 0 ? (
                  <TrendingUp className="h-8 w-8 text-[#10B981]" />
                ) : (
                  <TrendingDown className="h-8 w-8 text-[#EF4444]" />
                )}
              </div>
            </Card>
          </div>
        )}

        {view === 'dashboard' && metrics && <MetricsGrid metrics={metrics} />}
        {view === 'reports' && <ReportsView startDate={startDate} endDate={endDate} />}
        {view === 'calendar' && <CalendarView calendarData={calendarData} />}
        {view === 'trades' && <TradeList trades={trades} />}
      </div>

      <ImportDialog
        open={showImport}
        onClose={() => setShowImport(false)}
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}
