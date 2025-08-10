import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://127.0.0.1:8000';

async function proxy(req: NextRequest, parts: string[]) {
  const target = `${FASTAPI_URL}/api/${parts.join('/')}${new URL(req.url).search}`;
  
  try {
    const init: RequestInit = {
      method: req.method,
      headers: { 'content-type': req.headers.get('content-type') ?? '' },
      body: req.method === 'GET' || req.method === 'HEAD' ? undefined : await req.text(),
    };
    
    const res = await fetch(target, init);
    return new NextResponse(await res.text(), {
      status: res.status,
      headers: { 'content-type': res.headers.get('content-type') ?? 'application/json' },
    });
    
  } catch (error) {
    console.error('❌ Proxy error:', error);
    
    // Better error handling for connection issues
    if (error instanceof Error && 'code' in error && error.code === 'ECONNREFUSED') {
      return NextResponse.json(
        { 
          error: 'Python AI server is not running',
          message: 'Please start the Python server by running: python server.py',
          details: 'Make sure the server is running on http://localhost:8000'
        }, 
        { status: 503 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Proxy request failed',
        message: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path?: string[] }> }) {
  const params = await ctx.params;
  return proxy(req, params.path ?? []);
}

export async function POST(req: NextRequest, ctx: { params: Promise<{ path?: string[] }> }) {
  const params = await ctx.params;
  return proxy(req, params.path ?? []);
}

export async function PUT(req: NextRequest, ctx: { params: Promise<{ path?: string[] }> }) {
  const params = await ctx.params;
  return proxy(req, params.path ?? []);
}

export async function DELETE(req: NextRequest, ctx: { params: Promise<{ path?: string[] }> }) {
  const params = await ctx.params;
  return proxy(req, params.path ?? []);
}