import { NextResponse } from 'next/server';
import { tokenApiGet } from '@/lib/tokenApi';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type Row = {
  datetime: string; // "2025-05-29 15:00:00"
  open: number | string; high: number | string; low: number | string; close: number | string;
  volume?: number | string;
  ticker?: string; uaw?: number; transactions?: number;
};

export async function GET(req: Request) {
  try {
    const u = new URL(req.url);
    const contract = u.searchParams.get('contract'); // 0x…
    if (!contract) return NextResponse.json({ data: [] }, { status: 200 });

    const network_id = u.searchParams.get('network_id') || 'mainnet';          // arbitrum-one, bsc, matic, …
    const interval   = u.searchParams.get('interval')   || 'daily';            // hourly|4-hours|daily|weekly
    const startTime  = u.searchParams.get('startTime')  || undefined;
    const endTime    = u.searchParams.get('endTime')    || undefined;
    const limit      = u.searchParams.get('limit')      || '500';
    const page       = u.searchParams.get('page')       || '1';

    const json = await tokenApiGet<{ data: Row[] }>(`/ohlc/prices/evm/${contract}`, {
      network_id, interval, startTime, endTime, limit, page,
    });

    const data = (json.data || []).map((r) => ({
      time: Math.floor(new Date(r.datetime).getTime() / 1000),
      open: Number(r.open), high: Number(r.high), low: Number(r.low), close: Number(r.close),
      volume: r.volume != null ? Number(r.volume) : 0,
    }));

    return NextResponse.json({ data, source: 'thegraph-tokenapi' }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: String(e?.message || e) }, { status: 500 });
  }
}
