import { NextResponse } from 'next/server';
import { getCandles } from '@/lib/history';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const symbol = url.searchParams.get('symbol') || '';
    const interval = url.searchParams.get('interval') || '1h';
    const days = Number(url.searchParams.get('days') || '30');
    if (!symbol) return NextResponse.json([], { status: 200 });

    const data = await getCandles(symbol, interval, days);
    return NextResponse.json(data, { status: 200 });
  } catch (e: any) {
    return NextResponse.json({ error: String(e?.message || e) }, { status: 500 });
  }
}
