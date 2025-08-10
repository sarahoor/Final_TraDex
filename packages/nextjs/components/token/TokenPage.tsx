'use client';

import React, { useMemo } from 'react';
import { useCoinHistory } from '@/hooks/useCoinHistory';
import TokenHeader from '@/components/token/TokenHeader';
import CandleChart from '@/components/token/chart/CandleChart';

export default function TokenPage(props: {
  symbol: string;
  vs?: string;
  days?: number;
  interval?: string;
  useMock?: boolean;
}) {
  const symbol = useMemo(() => props.symbol?.toLowerCase?.() ?? '', [props.symbol]);
  const vs = props.vs ?? 'usd';
  const days = props.days ?? 30;
  const interval = props.interval ?? '1h';
  const useMock = props.useMock ?? false;

  const { data, error, isLoading } = useCoinHistory(symbol, vs, days, interval, useMock);

  if (error) return <div className="p-6">Failed to load: {String(error)}</div>;
  if (isLoading || !data) return <div className="p-6">Loading {symbol.toUpperCase()}…</div>;

  const last = data[data.length - 1]?.close;

  return (
    <main className="p-6 space-y-6">
      <TokenHeader
        symbol={symbol}
        vs={vs}
        days={days}
        interval={interval}
        useMock={useMock}
        last={last}
      />
      <CandleChart data={data} />
    </main>
  );
}
