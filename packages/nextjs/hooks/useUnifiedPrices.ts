'use client';

import useSWR from 'swr';
import type { MarketRow } from '@/components/markets/MarketTable';

type TokenPrice = { symbol: string; priceUSD: number };
type PoolInfo = { pair: string; tick: number };
type Snapshot = {
  tokens?: TokenPrice[];
  pools?: PoolInfo[];
  blockNumber?: number;
  secondsAgo?: number;
  error?: string;
};

export type UnifiedData = {
  rows: MarketRow[];
  pairs: PoolInfo[];
  raw: { uni?: Snapshot; sushi?: Snapshot; quick?: Snapshot; cake?: Snapshot };
};

const fetcher = async (url: string) => {
  const r = await fetch(url, { cache: 'no-store' });
  const j = await r.json();
  if (!r.ok) throw new Error(j?.error || `HTTP ${r.status}`);
  return j as Snapshot;
};

export function useUnifiedPrices(opts: {
  secondsAgo?: number;
  enabled: { uni: boolean; sushi: boolean; quick: boolean; cake: boolean };
  first?: number;
  refreshMs?: number;
}) {
  const { secondsAgo = 0, enabled, first = 300, refreshMs = 60_000 } = opts;

  const key = (base: string, on: boolean) =>
    on ? `${base}?secondsAgo=${secondsAgo}&first=${first}` : null;

  const {
    data: uni,   error: uniErr,   isLoading: uniLoading,
  } = useSWR<Snapshot>(key('/api/graph/uni', enabled.uni), fetcher, {
    revalidateOnFocus: false, dedupingInterval: refreshMs, refreshInterval: refreshMs,
  });

  const {
    data: sushi, error: sushiErr, isLoading: sushiLoading,
  } = useSWR<Snapshot>(key('/api/graph/sushi', enabled.sushi), fetcher, {
    revalidateOnFocus: false, dedupingInterval: refreshMs, refreshInterval: refreshMs,
  });

  const {
    data: quick, error: quickErr, isLoading: quickLoading,
  } = useSWR<Snapshot>(key('/api/graph/quickswap', enabled.quick), fetcher, {
    revalidateOnFocus: false, dedupingInterval: refreshMs, refreshInterval: refreshMs,
  });

  const {
    data: cake,  error: cakeErr,  isLoading: cakeLoading,
  } = useSWR<Snapshot>(key('/api/graph/pancake', enabled.cake), fetcher, {
    revalidateOnFocus: false, dedupingInterval: refreshMs, refreshInterval: refreshMs,
  });

  const isLoading =
    (enabled.uni && uniLoading) ||
    (enabled.sushi && sushiLoading) ||
    (enabled.quick && quickLoading) ||
    (enabled.cake && cakeLoading);

  const error = uniErr || sushiErr || quickErr || cakeErr;

  // Merge tokens by symbol with median aggregation
  type Acc = {
    symbol: string;
    vals: number[];
    byProtocol: Record<'uni' | 'sushi' | 'quick' | 'cake', number | undefined>;
  };
  const bySymbol: Record<string, Acc> = {};

  const add = (proto: keyof Acc['byProtocol'], snap?: Snapshot) => {
    if (!snap?.tokens) return;
    for (const t of snap.tokens) {
      const sym = (t.symbol || '').toUpperCase().trim();
      if (!sym) continue;
      if (!bySymbol[sym]) bySymbol[sym] = { symbol: sym, vals: [], byProtocol: { uni: undefined, sushi: undefined, quick: undefined, cake: undefined } };
      bySymbol[sym].vals.push(t.priceUSD);
      bySymbol[sym].byProtocol[proto] = t.priceUSD;
    }
  };

  add('uni', uni);
  add('sushi', sushi);
  add('quick', quick);
  add('cake', cake);

  // de-noise: hide absurd medians unless in allowed list
  const tooLarge = (sym: string, px: number) =>
    px > 1_000_000 && !['BTC', 'WBTC', 'TBTC', 'ETH', 'WETH', 'PAXG', 'RETH', 'STETH', 'WSTETH'].includes(sym);

  const rows: MarketRow[] = Object.values(bySymbol).map(v => {
    const sorted = v.vals.slice().sort((a, b) => a - b);
    const median = sorted.length ? sorted[Math.floor(sorted.length / 2)] : null;
    const finalPrice = median != null && !tooLarge(v.symbol, median) ? median : null;
    return { symbol: v.symbol, price: finalPrice, byProtocol: v.byProtocol };
  });

  // Merge pairs (already limited server-side)
  const pairs: PoolInfo[] = [
    ...(uni?.pools || []),
    ...(sushi?.pools || []),
    ...(quick?.pools || []),
    ...(cake?.pools || []),
  ];

  return {
    data: { rows, pairs, raw: { uni, sushi, quick, cake } } as UnifiedData,
    isLoading,
    error,
  };
}
