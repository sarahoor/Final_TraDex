export function formatPrice(n: number | null | undefined) {
  if (n == null || !isFinite(n)) return '—';
  // very small numbers: show up to 8 decimals; larger: compact
  if (Math.abs(n) < 0.000001) return n.toExponential(2).replace('+', '');
  if (Math.abs(n) < 1) return n.toLocaleString(undefined, { maximumFractionDigits: 8 });
  // compact for big ones
  return Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 3 }).format(n);
}
