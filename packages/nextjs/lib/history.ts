// Server-only helpers to fetch candles from Binance, fallback to CoinGecko

type OHLC = { time: number; open: number; high: number; low: number; close: number; volume: number };

const BINANCE_INTERVAL_MAP: Record<string, string> = {
  '1m': '1m',
  '5m': '5m',
  '30m': '30m',
  '1h': '1h',
  '1d': '1d',
};

function guessBinanceSymbol(sym: string): string {
  // naive: SYMBOL + USDT, uppercase
  return `${sym}`.toUpperCase().replace(/[^A-Z0-9]/g, '') + 'USDT';
}

export async function fetchCandlesBinance(symbol: string, interval: string, days: number): Promise<OHLC[] | null> {
  const binanceInterval = BINANCE_INTERVAL_MAP[interval] ?? '1h';
  const start = Date.now() - days * 24 * 60 * 60 * 1000;
  const market = guessBinanceSymbol(symbol);
  const url = `https://api.binance.com/api/v3/klines?symbol=${market}&interval=${binanceInterval}&startTime=${start}`;
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) return null;
  const arr = (await res.json()) as any[];
  if (!Array.isArray(arr)) return null;
  return arr.map(k => ({
    time: Math.floor(k[0] / 1000),
    open: +k[1], high: +k[2], low: +k[3], close: +k[4], volume: +k[5],
  }));
}

async function resolveCoingeckoId(symbol: string): Promise<string | null> {
  // try simple search endpoint
  const q = symbol.toLowerCase();
  const r = await fetch(`https://api.coingecko.com/api/v3/search?query=${encodeURIComponent(q)}`, { cache: 'no-store' });
  if (!r.ok) return null;
  const j = await r.json();
  const coin = j?.coins?.find((c: any) => c?.symbol?.toLowerCase() === q) || j?.coins?.[0];
  return coin?.id || null;
}

export async function fetchCandlesCoingecko(symbol: string, interval: string, days: number): Promise<OHLC[] | null> {
  // CG returns prices (no OHLC). Build "area-style" OHLC where o=h=l=c
  const id = await resolveCoingeckoId(symbol);
  if (!id) return null;

  // CG intervals are auto; days supports integers or 'max'
  const vs = 'usd';
  const url = `https://api.coingecko.com/api/v3/coins/${id}/market_chart?vs_currency=${vs}&days=${days}`;
  const r = await fetch(url, { cache: 'no-store' });
  if (!r.ok) return null;
  const j = await r.json();
  const prices: [number, number][] = j?.prices || [];
  if (!prices.length) return null;

  return prices.map(([ms, p]) => {
    const v = Number(p);
    return { time: Math.floor(ms / 1000), open: v, high: v, low: v, close: v, volume: 0 };
  });
}

export async function getCandles(symbol: string, interval: string, days: number): Promise<OHLC[]> {
  const bin = await fetchCandlesBinance(symbol, interval, days).catch(() => null);
  if (bin && bin.length) return bin;
  const cg = await fetchCandlesCoingecko(symbol, interval, days).catch(() => null);
  return cg || [];
}
