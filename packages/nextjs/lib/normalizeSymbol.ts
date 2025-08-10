const MAP: Record<string, string> = {
  // common names → Binance tickers
  ethereum: 'ETH',
  ether: 'ETH',
  bitcoin: 'BTC',
  solana: 'SOL',
  polygon: 'MATIC',
  bnb: 'BNB',
  ripple: 'XRP',
  cardano: 'ADA',
  dogecoin: 'DOGE',
  litecoin: 'LTC',
  chainlink: 'LINK',
  uniswap: 'UNI',
  aave: 'AAVE',
  pancakeswap: 'CAKE',
  sushi: 'SUSHI',
};

export function normalizeSymbol(input: string) {
  if (!input) return '';
  const s = input.trim().toLowerCase();
  // if already a 0x… address, return as-is (for Token API later)
  if (/^0x[a-f0-9]{40}$/i.test(s)) return s;
  // if looks like a ticker (3–6 chars letters), keep uppercase
  if (/^[a-z]{2,8}$/i.test(s) && !MAP[s]) return s.toUpperCase();
  return (MAP[s] ?? s).toUpperCase();
}
