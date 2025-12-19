import React from 'react';
import { Card } from '@/components/ui/card';
import { formatCurrency } from '../utils/formatters';

export const MetricsGrid = ({ metrics }) => {
  const metricCards = [
    {
      label: 'Average Daily P&L',
      value: formatCurrency(metrics.avg_daily_pnl),
      color: metrics.avg_daily_pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]',
      testId: 'avg-daily-pnl'
    },
    {
      label: 'Total Trades',
      value: metrics.total_trades,
      color: 'text-[#FAFAFA]',
      testId: 'total-trades'
    },
    {
      label: 'Winning Trades',
      value: metrics.winning_trades,
      color: 'text-[#10B981]',
      testId: 'winning-trades'
    },
    {
      label: 'Losing Trades',
      value: metrics.losing_trades,
      color: 'text-[#EF4444]',
      testId: 'losing-trades'
    },
    {
      label: 'Scratch Trades',
      value: metrics.scratch_trades,
      color: 'text-[#A1A1AA]',
      testId: 'scratch-trades'
    },
    {
      label: 'Loss Rate',
      value: `${(metrics.loss_rate * 100).toFixed(1)}%`,
      color: 'text-[#EF4444]',
      testId: 'loss-rate'
    },
    {
      label: 'Average Winning Trade',
      value: formatCurrency(metrics.avg_winning_trade),
      color: 'text-[#10B981]',
      testId: 'avg-winning-trade'
    },
    {
      label: 'Average Losing Trade',
      value: formatCurrency(metrics.avg_losing_trade),
      color: 'text-[#EF4444]',
      testId: 'avg-losing-trade'
    },
    {
      label: 'Largest Gain',
      value: formatCurrency(metrics.largest_gain),
      color: 'text-[#10B981]',
      testId: 'largest-gain'
    },
    {
      label: 'Largest Loss',
      value: formatCurrency(metrics.largest_loss),
      color: 'text-[#EF4444]',
      testId: 'largest-loss'
    },
    {
      label: 'Max Consecutive Wins',
      value: metrics.max_consecutive_wins,
      color: 'text-[#10B981]',
      testId: 'max-consecutive-wins'
    },
    {
      label: 'Max Consecutive Losses',
      value: metrics.max_consecutive_losses,
      color: 'text-[#EF4444]',
      testId: 'max-consecutive-losses'
    },
    {
      label: 'Avg Hold (Winning)',
      value: metrics.avg_hold_time_winning,
      color: 'text-[#10B981]',
      testId: 'avg-hold-winning'
    },
    {
      label: 'Avg Hold (Losing)',
      value: metrics.avg_hold_time_losing,
      color: 'text-[#EF4444]',
      testId: 'avg-hold-losing'
    },
    {
      label: 'Avg Hold (Scratch)',
      value: metrics.avg_hold_time_scratch,
      color: 'text-[#A1A1AA]',
      testId: 'avg-hold-scratch'
    },
    {
      label: 'Scratch Rate',
      value: `${(metrics.scratch_rate * 100).toFixed(1)}%`,
      color: 'text-[#A1A1AA]',
      testId: 'scratch-rate'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="metrics-grid">
      {metricCards.map((metric, index) => (
        <Card
          key={index}
          className="bg-[#18181B] border-[#27272A] p-4 rounded-sm stat-card hover:border-[#3F3F46] transition-colors"
        >
          <p className="text-[#A1A1AA] text-xs mb-2 font-['Inter'] uppercase tracking-wide">
            {metric.label}
          </p>
          <p className={`text-2xl font-bold font-['JetBrains_Mono'] ${metric.color}`} data-testid={metric.testId}>
            {metric.value}
          </p>
        </Card>
      ))}
    </div>
  );
};

export default MetricsGrid;
