import type { History } from '@/types/market';
import type { UTCTimestamp } from 'lightweight-charts';

const json = async (url: string) => {
  const r = await fetch(url, { next: { revalidate: 30 } });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
};

// symbol must be a CoinGecko "coin id" (e.g., 'bitcoin', 'ethereum')
export async function fromCoinGecko(
  symbol: string,
  vs = 'usd',
  days = 30
): Promise<History> {
  const data = await json(
    `https://api.coingecko.com/api/v3/coins/${symbol}/ohlc?vs_currency=${vs}&days=${days}`
  );
  // [[timestamp, open, high, low, close], ...]
  return (data as [number, number, number, number, number][])
    .map(([t, o, h, l, c]) => ({
      time: Math.floor(t / 1000) as UTCTimestamp,
      open: o,
      high: h,
      low: l,
      close: c,
    }));
}
