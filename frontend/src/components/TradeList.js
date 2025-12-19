import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { formatCurrency } from '../utils/formatters';

export const TradeList = ({ trades }) => {
  const [sortField, setSortField] = useState('trade_date');
  const [sortDirection, setSortDirection] = useState('desc');

  const sortedTrades = [...trades].sort((a, b) => {
    let aVal, bVal;

    switch (sortField) {
      case 'trade_date':
        aVal = new Date(a.trade_date);
        bVal = new Date(b.trade_date);
        break;
      case 'pnl':
        aVal = a.pnl;
        bVal = b.pnl;
        break;
      case 'symbol':
        aVal = a.symbol;
        bVal = b.symbol;
        break;
      default:
        return 0;
    }

    if (sortDirection === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  return (
    <Card className="bg-[#18181B] border-[#27272A] rounded-sm overflow-hidden" data-testid="trade-list">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[#27272A]">
            <tr>
              <th
                className="text-left p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium cursor-pointer hover:text-[#FAFAFA]"
                onClick={() => handleSort('trade_date')}
              >
                Date {sortField === 'trade_date' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th
                className="text-left p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium cursor-pointer hover:text-[#FAFAFA]"
                onClick={() => handleSort('symbol')}
              >
                Symbol {sortField === 'symbol' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">
                Side
              </th>
              <th className="text-right p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">
                Entry
              </th>
              <th className="text-right p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">
                Exit
              </th>
              <th className="text-right p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">
                Qty
              </th>
              <th
                className="text-right p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium cursor-pointer hover:text-[#FAFAFA]"
                onClick={() => handleSort('pnl')}
              >
                P&L {sortField === 'pnl' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th className="text-left p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">
                Result
              </th>
              <th className="text-right p-4 text-xs uppercase tracking-wider text-[#A1A1AA] font-['Inter'] font-medium">
                Hold Time
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedTrades.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center p-8 text-[#A1A1AA] font-['Inter']">
                  No trades found. Import your trading data to get started.
                </td>
              </tr>
            ) : (
              sortedTrades.map((trade, index) => (
                <tr
                  key={index}
                  className="border-t border-[#27272A] hover:bg-[#27272A]/30 transition-colors"
                  data-testid={`trade-row-${index}`}
                >
                  <td className="p-4 font-['JetBrains_Mono'] text-sm text-[#FAFAFA]">
                    {trade.trade_date}
                  </td>
                  <td className="p-4 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] font-medium">
                    {trade.symbol}
                  </td>
                  <td className="p-4 font-['Inter'] text-sm text-[#A1A1AA]">
                    {trade.side}
                  </td>
                  <td className="p-4 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">
                    ${trade.entry_price.toFixed(2)}
                    <div className="text-xs text-[#71717A]">{trade.entry_time}</div>
                  </td>
                  <td className="p-4 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">
                    ${trade.exit_price.toFixed(2)}
                    <div className="text-xs text-[#71717A]">{trade.exit_time}</div>
                  </td>
                  <td className="p-4 font-['JetBrains_Mono'] text-sm text-[#FAFAFA] text-right">
                    {trade.quantity}
                  </td>
                  <td
                    className={`p-4 font-['JetBrains_Mono'] text-sm font-bold text-right ${
                      trade.pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'
                    }`}
                  >
                    {formatCurrency(trade.pnl)}
                  </td>
                  <td className="p-4">
                    <span
                      className={`inline-block px-2 py-1 rounded-sm text-xs font-['Inter'] font-medium ${
                        trade.result === 'Win'
                          ? 'bg-[#10B981]/20 text-[#10B981]'
                          : trade.result === 'Lose'
                          ? 'bg-[#EF4444]/20 text-[#EF4444]'
                          : 'bg-[#A1A1AA]/20 text-[#A1A1AA]'
                      }`}
                    >
                      {trade.result}
                    </span>
                  </td>
                  <td className="p-4 font-['JetBrains_Mono'] text-sm text-[#A1A1AA] text-right">
                    {trade.hold_time}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

export default TradeList;
