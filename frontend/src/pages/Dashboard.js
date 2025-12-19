import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, TrendingUp, TrendingDown, Calendar as CalendarIcon, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
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
  const [view, setView] = useState('dashboard'); // dashboard, calendar, trades, reports

  const fetchData = async () => {
    try {
      setLoading(true);
      const [metricsRes, tradesRes, calendarRes] = await Promise.all([
        axios.get(`${API}/dashboard-metrics`),
        axios.get(`${API}/trades`),
        axios.get(`${API}/calendar-data`)
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
  }, []);

  const handleImportSuccess = () => {
    setShowImport(false);
    fetchData();
    toast.success('Trades imported successfully!');
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
      
      {/* Header */}
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
          <Button
            onClick={() => setShowImport(true)}
            className="bg-[#FAFAFA] text-[#18181B] hover:bg-[#E4E4E7] rounded-sm font-['JetBrains_Mono'] font-medium"
            data-testid="import-button"
          >
            <Upload className="mr-2 h-4 w-4" />
            Import CSV
          </Button>
        </div>

        {/* View Tabs */}
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

        {/* Quick Stats Bar */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[#A1A1AA] text-sm mb-1 font-['Inter']">Total P&L</p>
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
              <p className="text-[#A1A1AA] text-sm mb-1 font-['Inter']">Avg Trade P&L</p>
              <p
                className={`text-3xl font-bold font-['JetBrains_Mono'] ${
                  metrics.avg_trade_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                }`}
                data-testid="avg-trade-pnl"
              >
                {formatCurrency(metrics.avg_trade_pnl)}
              </p>
            </Card>
          </div>
        )}

        {/* Main Content */}
        {view === 'dashboard' && metrics && <MetricsGrid metrics={metrics} />}
        {view === 'reports' && <ReportsView />}
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
