const BASE = 'https://token-api.thegraph.com';

export async function tokenApiGet<T>(path: string, qs?: Record<string, string | number | undefined>) {
  const url = new URL(path, BASE);
  if (qs) for (const [k, v] of Object.entries(qs)) if (v !== undefined) url.searchParams.set(k, String(v));
  const r = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${process.env.TOKEN_API_JWT}` },
    cache: 'no-store',
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j?.error || j?.message || `HTTP ${r.status}`);
  return j as T;
}
