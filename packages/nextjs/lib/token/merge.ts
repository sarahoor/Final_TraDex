import type { History, OHLC } from '@/types/market';
import type { UTCTimestamp } from 'lightweight-charts';

export function mergeHistories(histories: History[]): History {
  const buckets = new Map<number, OHLC[]>();

  for (const h of histories) {
    for (const c of h) {
      const ts = Number(c.time);
      if (!buckets.has(ts)) buckets.set(ts, []);
      buckets.get(ts)!.push(c);
    }
  }

  const merged: History = [];
  for (const [ts, arr] of buckets) {
    arr.sort((a, b) => (a.time as number) - (b.time as number));
    const open = arr[0].open;
    const close = arr[arr.length - 1].close;
    const high = Math.max(...arr.map(c => c.high));
    const low = Math.min(...arr.map(c => c.low));
    const closes = [...arr.map(c => c.close)].sort((a, b) => a - b);
    const medianClose = closes[Math.floor(closes.length / 2)];
    merged.push({ time: ts as UTCTimestamp, open, high, low, close: medianClose });
  }

  return merged.sort((a, b) => (a.time as number) - (b.time as number));
}
