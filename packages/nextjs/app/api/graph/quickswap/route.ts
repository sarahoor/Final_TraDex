import { NextResponse } from 'next/server';
import { fetchQuickSwapV3Snapshot } from '@/lib/markets/quickswapV3';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

let cache: { key: string; at: number; data: any } | null = null;

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const secondsAgo = Number(url.searchParams.get('secondsAgo') ?? '0');
    const first = Number(url.searchParams.get('first') ?? '300');
    const key = `quick:${secondsAgo}:${first}`;
    if (cache && cache.key === key && Date.now() - cache.at < 60_000) {
      return NextResponse.json(cache.data, { status: 200 });
    }
    const data = await fetchQuickSwapV3Snapshot(secondsAgo, first);
    cache = { key, at: Date.now(), data };
    return NextResponse.json(data, { status: 200 });
  } catch (e: any) {
    console.error('QUICK route error:', e);
    return NextResponse.json({ error: String(e?.message || e) }, { status: 500 });
  }
}
