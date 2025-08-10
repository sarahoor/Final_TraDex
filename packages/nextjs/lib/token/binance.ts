import type { History } from '@/types/market';
import type { UTCTimestamp } from 'lightweight-charts';

const json = async (url: string) => {
  const r = await fetch(url, { next: { revalidate: 30 } });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
};

// 'symbol' like 'btc' -> BTCUSDT (default)
// change quote if needed (e.g., 'BUSD')
export async function fromBinance(
  symbol: string,
  interval = '1h',
  quote = 'USDT',
  limit = 500
): Promise<History> {
  const pair = `${symbol.toUpperCase()}${quote.toUpperCase()}`;
  const data = await json(
    `https://api.binance.com/api/v3/klines?symbol=${pair}&interval=${interval}&limit=${limit}`
  );
  // [ openTime, open, high, low, close, volume, closeTime, ... ]
  return (data as any[]).map(k => ({
    time: Math.floor(k[0] / 1000) as UTCTimestamp,
    open: +k[1],
    high: +k[2],
    low: +k[3],
    close: +k[4],
    volume: +k[5],
  }));
}
