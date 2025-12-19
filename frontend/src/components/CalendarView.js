import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '../utils/formatters';

export const CalendarView = ({ calendarData }) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentDate);

  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const getDataForDate = (day) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return calendarData.find(d => d.date === dateStr);
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Generate calendar days
  const calendarDays = [];
  
  // Empty cells before first day
  for (let i = 0; i < startingDayOfWeek; i++) {
    calendarDays.push({ isEmpty: true, key: `empty-${i}` });
  }
  
  // Actual days
  for (let day = 1; day <= daysInMonth; day++) {
    const data = getDataForDate(day);
    calendarDays.push({
      day,
      data,
      key: `day-${day}`
    });
  }

  return (
    <div data-testid="calendar-view">
      <Card className="bg-[#18181B] border-[#27272A] p-6 rounded-sm">
        {/* Calendar Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold font-['JetBrains_Mono']" data-testid="calendar-month-year">
            {monthNames[month]} {year}
          </h2>
          <div className="flex gap-2">
            <Button
              onClick={prevMonth}
              variant="outline"
              size="icon"
              className="bg-[#27272A] border-[#3F3F46] hover:bg-[#3F3F46] rounded-sm"
              data-testid="prev-month-button"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              onClick={nextMonth}
              variant="outline"
              size="icon"
              className="bg-[#27272A] border-[#3F3F46] hover:bg-[#3F3F46] rounded-sm"
              data-testid="next-month-button"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Day Names */}
        <div className="grid grid-cols-7 gap-2 mb-2">
          {dayNames.map(day => (
            <div
              key={day}
              className="text-center text-[#A1A1AA] text-xs font-['JetBrains_Mono'] font-medium uppercase tracking-wider py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-2">
          {calendarDays.map(({ isEmpty, day, data, key }) => {
            if (isEmpty) {
              return <div key={key} className="aspect-square" />;
            }

            const hasTrades = data && data.trade_count > 0;
            const pnl = data ? data.pnl : 0;
            const isProfit = pnl > 0;
            const isLoss = pnl < 0;

            return (
              <div
                key={key}
                className={`
                  aspect-square p-2 rounded-sm border
                  ${
                    hasTrades
                      ? isProfit
                        ? 'bg-[#10B981]/10 border-[#10B981]/30'
                        : isLoss
                        ? 'bg-[#EF4444]/10 border-[#EF4444]/30'
                        : 'border-[#27272A]'
                      : 'border-[#27272A]'
                  }
                  calendar-day cursor-pointer
                `}
                data-testid={`calendar-day-${day}`}
              >
                <div className="flex flex-col h-full">
                  <div className="text-xs font-['JetBrains_Mono'] text-[#A1A1AA] mb-1">
                    {day}
                  </div>
                  {hasTrades && (
                    <div className="flex-1 flex flex-col justify-center">
                      <div
                        className={`text-xs font-['JetBrains_Mono'] font-bold ${
                          isProfit ? 'text-[#10B981]' : isLoss ? 'text-[#EF4444]' : 'text-[#A1A1AA]'
                        }`}
                      >
                        {formatCurrency(pnl)}
                      </div>
                      <div className="text-[10px] text-[#71717A] font-['Inter'] mt-1">
                        {data.trade_count} {data.trade_count === 1 ? 'trade' : 'trades'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

export default CalendarView;
