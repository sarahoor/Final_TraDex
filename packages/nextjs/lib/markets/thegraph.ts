// Small helper to call The Graph Gateway with your API key (server-side only)
type GraphResponse<T> = { data: T; errors?: any };

export const AVG_BLOCK_TIME = 12;

function subgraphUrl(id: string) {
  const key = process.env.THEGRAPH_API_KEY || process.env.ABI_KEY; // fallback to your current name
  if (!key) throw new Error('Missing THEGRAPH_API_KEY (or ABI_KEY) in env');
  return `https://gateway.thegraph.com/api/${key}/subgraphs/id/${id}`;
}

export async function gqlFetch<T>(subgraphId: string, query: string, variables?: Record<string, any>): Promise<T> {
  const res = await fetch(subgraphUrl(subgraphId), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(variables ? { query, variables } : { query }),
    cache: 'no-store',
  });
  const json = (await res.json()) as GraphResponse<T>;
  if (json.errors) throw new Error(JSON.stringify(json.errors));
  return json.data;
}
