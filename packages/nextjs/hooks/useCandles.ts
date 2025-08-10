'use client';

import useSWR from 'swr';
import { normalizeSymbol } from '@/lib/normalizeSymbol';

export type Candle = { time: number; open: number; high: number; low: number; close: number; volume: number };
export type Interval = '1m' | '5m' | '30m' | '1h' | '1d';

const fetcher = (url: string) => fetch(url, { cache: 'no-store' }).then(r => r.json());

// ...
export function useCandles(symbol: string, interval: Interval, days: number) {
  const sym = normalizeSymbol(symbol);
  const key = sym ? `/api/history?symbol=${encodeURIComponent(sym)}&interval=${interval}&days=${days}` : null;
  const { data, error, isLoading } = useSWR<Candle[]>(key, fetcher, {
    refreshInterval: 60_000, // auto refresh every 1 min
    revalidateOnFocus: false,
  });

  return { candles: data ?? [], isLoading, error };
}
