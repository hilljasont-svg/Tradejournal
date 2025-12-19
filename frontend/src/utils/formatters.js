export const formatCurrency = (value) => {
  const num = parseFloat(value);
  if (isNaN(num)) return '$0.00';
  
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
  
  return formatted;
};

export const formatPercent = (value) => {
  const num = parseFloat(value);
  if (isNaN(num)) return '0.0%';
  
  return `${(num * 100).toFixed(1)}%`;
};

export const formatNumber = (value) => {
  const num = parseFloat(value);
  if (isNaN(num)) return '0';
  
  return new Intl.NumberFormat('en-US').format(num);
};
