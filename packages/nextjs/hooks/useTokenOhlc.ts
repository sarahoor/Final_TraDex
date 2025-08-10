'use client';
import useSWR from 'swr';

export type Candle = { time: number; open: number; high: number; low: number; close: number; volume: number };
type Resp = { data: Candle[]; source: string };

const fetcher = (u: string) => fetch(u, { cache: 'no-store' }).then(r => r.json());

export type OhlcInterval = 'hourly' | '4-hours' | 'daily' | 'weekly';

export function useTokenOhlc(contract: string, p?: {
  network_id?: string; interval?: OhlcInterval; startTime?: number; endTime?: number; limit?: number; page?: number;
}) {
  const { network_id = 'mainnet', interval = 'daily', startTime, endTime, limit = 500, page = 1 } = p || {};
  const q = new URLSearchParams({
    contract, network_id, interval, limit: String(limit), page: String(page),
    ...(startTime ? { startTime: String(startTime) } : {}),
    ...(endTime ? { endTime: String(endTime) } : {}),
  }).toString();

  const key = contract ? `/api/token/ohlc?${q}` : null;
  const { data, error, isLoading } = useSWR<Resp>(key, fetcher, { refreshInterval: 60_000, revalidateOnFocus: false });

  return { candles: data?.data ?? [], source: data?.source ?? 'thegraph-tokenapi', isLoading, error };
}
