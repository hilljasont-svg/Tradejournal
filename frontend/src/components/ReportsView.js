import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from '@/components/ui/card';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { formatCurrency } from '../utils/formatters';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ReportsView = () => {
  const [cumulativePnl, setCumulativePnl] = useState([]);
  const [timeAnalysis, setTimeAnalysis] = useState([]);
  const [symbolPerformance, setSymbolPerformance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const [cumulativeRes, timeRes, symbolRes] = await Promise.all([
          axios.get(`${API}/cumulative-pnl`),
          axios.get(`${API}/time-analysis`),
          axios.get(`${API}/symbol-performance`)
        ]);
        
        setCumulativePnl(cumulativeRes.data);
        setTimeAnalysis(timeRes.data);
        setSymbolPerformance(symbolRes.data);
      } catch (error) {
        console.error('Error fetching report data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReportData();
  }, []);

  if (loading) {
    return (
      <div className="text-[#FAFAFA] font-['JetBrains_Mono'] text-center py-8">
        Loading reports...
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#18181B] border border-[#27272A] p-3 rounded-sm">
          <p className="text-[#A1A1AA] text-xs font-['Inter'] mb-1">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="font-['JetBrains_Mono'] text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' && entry.name.includes('P&L') 
                ? formatCurrency(entry.value) 
                : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Format time analysis data
  const formattedTimeData = timeAnalysis.map(item => ({
    ...item,
    hourLabel: `${item.hour.toString().padStart(2, '0')}:00`,
    winRatePercent: (item.win_rate * 100).toFixed(1)
  }));

  return (
    <div className="space-y-8" data-testid="reports-view">
      {/* Cumulative P&L Trend */}
      <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
        <h2 className="text-xl font-bold font-['JetBrains_Mono'] mb-6 text-[#FAFAFA]">
          Cumulative P&L Trend
        </h2>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={cumulativePnl}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
            <XAxis 
              dataKey="date" 
              stroke="#A1A1AA"
              style={{ fontSize: '12px', fontFamily: 'JetBrains Mono' }}
              tick={{ fill: '#A1A1AA' }}
            />
            <YAxis 
              stroke="#A1A1AA"
              style={{ fontSize: '12px', fontFamily: 'JetBrains Mono' }}
              tick={{ fill: '#A1A1AA' }}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontFamily: 'Inter', fontSize: '12px' }}
              iconType="line"
            />
            <Line 
              type="monotone" 
              dataKey="cumulative_pnl" 
              stroke="#10B981" 
              strokeWidth={2}
              name="Cumulative P&L"
              dot={{ fill: '#10B981', r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Trading Performance by Hour */}
      <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
        <h2 className="text-xl font-bold font-['JetBrains_Mono'] mb-2 text-[#FAFAFA]">
          Performance by Trading Hour
        </h2>
        <p className="text-[#A1A1AA] text-sm font-['Inter'] mb-6">
          Identify your most profitable trading times
        </p>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* P&L by Hour */}
          <div>
            <h3 className="text-sm font-medium font-['Inter'] text-[#A1A1AA] mb-4">Average P&L by Hour</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={formattedTimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                <XAxis 
                  dataKey="hourLabel" 
                  stroke="#A1A1AA"
                  style={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  tick={{ fill: '#A1A1AA' }}
                />
                <YAxis 
                  stroke="#A1A1AA"
                  style={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  tick={{ fill: '#A1A1AA' }}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="avg_pnl" name="Avg P&L" radius={[4, 4, 0, 0]}>
                  {formattedTimeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.avg_pnl >= 0 ? '#10B981' : '#EF4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Win Rate by Hour */}
          <div>
            <h3 className="text-sm font-medium font-['Inter'] text-[#A1A1AA] mb-4">Win Rate by Hour</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={formattedTimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                <XAxis 
                  dataKey="hourLabel" 
                  stroke="#A1A1AA"
                  style={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  tick={{ fill: '#A1A1AA' }}
                />
                <YAxis 
                  stroke="#A1A1AA"
                  style={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }}
                  tick={{ fill: '#A1A1AA' }}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="winRatePercent" fill="#3B82F6" name="Win Rate %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Time Analysis Table */}
        <div className="mt-6 overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#27272A]">
              <tr>
                <th className="text-left p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Hour</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Trades</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Total P&L</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Avg P&L</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {formattedTimeData
                .filter(item => item.trade_count > 0)
                .sort((a, b) => b.avg_pnl - a.avg_pnl)
                .map((item, index) => (
                  <tr key={index} className="border-t border-[#27272A] hover:bg-[#27272A]/30 transition-colors">
                    <td className="p-3 font-['JetBrains_Mono'] text-sm text-[#FAFAFA]">{item.hourLabel}</td>
                    <td className="p-3 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">{item.trade_count}</td>
                    <td className={`p-3 font-['JetBrains_Mono'] text-sm font-medium text-right ${
                      item.total_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                    }`}>
                      {formatCurrency(item.total_pnl)}
                    </td>
                    <td className={`p-3 font-['JetBrains_Mono'] text-sm font-medium text-right ${
                      item.avg_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                    }`}>
                      {formatCurrency(item.avg_pnl)}
                    </td>
                    <td className="p-3 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">
                      {item.winRatePercent}%
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Symbol Performance */}
      <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
        <h2 className="text-xl font-bold font-['JetBrains_Mono'] mb-2 text-[#FAFAFA]">
          Performance by Symbol
        </h2>
        <p className="text-[#A1A1AA] text-sm font-['Inter'] mb-6">
          Your best and worst performing symbols
        </p>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#27272A]">
              <tr>
                <th className="text-left p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Symbol</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Trades</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Total P&L</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Avg P&L</th>
                <th className="text-right p-3 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">Win Rate</th>
              </tr>
            </thead>
            <tbody>
              {symbolPerformance.map((item, index) => (
                <tr key={index} className="border-t border-[#27272A] hover:bg-[#27272A]/30 transition-colors">
                  <td className="p-3 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] font-medium">{item.symbol}</td>
                  <td className="p-3 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">{item.trade_count}</td>
                  <td className={`p-3 font-['JetBrains_Mono'] text-sm font-bold text-right ${
                    item.total_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                  }`}>
                    {formatCurrency(item.total_pnl)}
                  </td>
                  <td className={`p-3 font-['JetBrains_Mono'] text-sm font-medium text-right ${
                    item.avg_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                  }`}>
                    {formatCurrency(item.avg_pnl)}
                  </td>
                  <td className="p-3 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">
                    {(item.win_rate * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ReportsView;
