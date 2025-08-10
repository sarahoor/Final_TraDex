'use client';

export default function TokenHeader(props: {
  symbol: string;
  vs: string;
  days: number;
  interval: string;
  useMock: boolean;
  last?: number;
}) {
  const { symbol, vs, days, interval, useMock, last } = props;

  return (
    <header className="space-y-1">
      <h1 className="text-2xl font-semibold uppercase tracking-wide">{symbol}</h1>
      <p className="opacity-70 text-sm">
        {useMock ? 'Mock data' : 'Aggregated OHLC from CoinGecko + Binance'}
      </p>
      <p className="text-xl">
        Last:{' '}
        {(last ?? 0).toLocaleString(undefined, { maximumFractionDigits: 8 })}{' '}
        {vs.toUpperCase()}
      </p>
      <div className="text-sm opacity-70">
        Params: days={days}, interval={interval}, vs={vs}, mock={String(useMock)}
      </div>
    </header>
  );
}
