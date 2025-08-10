// packages/nextjs/app/api/env-check/route.ts
import { NextResponse } from 'next/server';
export const runtime = 'nodejs';
export async function GET() {
  return NextResponse.json({
    has_ABI_KEY: !!process.env.ABI_KEY,
    has_THEGRAPH_API_KEY: !!process.env.THEGRAPH_API_KEY,
  });
}
