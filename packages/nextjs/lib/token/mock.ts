import type { History } from '@/types/market';
import type { UTCTimestamp } from 'lightweight-charts';

export function genMock(symbol: string, days = 30, interval = '1h'): History {
  const now = Math.floor(Date.now() / 1000);
  const step =
    interval === '1m' ? 60 :
    interval === '5m' ? 300 :
    interval === '15m' ? 900 :
    interval === '4h' ? 14400 :
    interval === '1d' ? 86400 : 3600;

  const n = Math.min(1000, Math.floor((days * 86400) / step));
  let seed = Array.from(symbol).reduce((a, c) => a + c.charCodeAt(0), 100);
  const rand = () => ((seed = (seed * 1664525 + 1013904223) % 2 ** 32) / 2 ** 32);

  let price = 100 + (rand() - 0.5) * 5;
  const out: History = [];
  for (let i = n; i >= 1; i--) {
    const t = (now - i * step) as UTCTimestamp;
    const drift = (rand() - 0.5) * 0.6;
    const vol = 0.8 + rand() * 0.6;

    const o = price;
    const h = o + Math.abs(drift) * vol;
    const l = o - Math.abs(drift) * vol;
    const c = o + drift;
    price = Math.max(0.0001, c);

    out.push({
      time: t,
      open: +o.toFixed(4),
      high: +h.toFixed(4),
      low: +l.toFixed(4),
      close: +c.toFixed(4),
    });
  }
  return out;
}
