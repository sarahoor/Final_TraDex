import { AVG_BLOCK_TIME, gqlFetch } from './thegraph';

// QuickSwap v3 (Polygon) subgraph id
const QUICK_V3_ID = 'FqsRcH1XqSjqVx9GRTvEJe959aCbKrcyGgDWBrUkG24g';

type Bundle = { maticPriceUSD: string };
type PoolToken = { symbol: string };
type Pool = { token0: PoolToken; token1: PoolToken; tick: string };

async function getCurrentBlock(): Promise<number> {
  const q = `{ _meta { block { number } } }`;
  const d = await gqlFetch<{ _meta: { block: { number: number } } }>(QUICK_V3_ID, q);
  return d._meta.block.number;
}

async function basePriceUSD(bn: number): Promise<number> {
  const q = `query($bn:Int!){ bundles(first:1, block:{number:$bn}){ maticPriceUSD } }`;
  const d = await gqlFetch<{ bundles: Bundle[] }>(QUICK_V3_ID, q, { bn });
  return Number(d.bundles[0].maticPriceUSD);
}

/** Try tokens with derivedMatic (common on Polygon v3). */
async function topTokensDerivedMatic(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    tokens(
      first:$first,
      block:{number:$bn},
      orderBy: totalValueLockedUSD,
      orderDirection: desc
    ){
      symbol
      derivedMatic
    }
  }`;
  const d = await gqlFetch<{ tokens: { symbol: string; derivedMatic: string | null }[] }>(
    QUICK_V3_ID, q, { bn, first }
  );
  return d.tokens.map(t => ({ symbol: t.symbol, derivedMatic: t.derivedMatic }));
}

/** Fallback: some schemas expose derivedUSD directly. */
async function topTokensDerivedUSD(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    tokens(
      first:$first,
      block:{number:$bn},
      orderBy: totalValueLockedUSD,
      orderDirection: desc
    ){
      symbol
      derivedUSD
    }
  }`;
  const d = await gqlFetch<{ tokens: { symbol: string; derivedUSD: string | null }[] }>(
    QUICK_V3_ID, q, { bn, first }
  );
  return d.tokens.map(t => ({ symbol: t.symbol, derivedUSD: t.derivedUSD }));
}

async function topPools(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    pools(
      first:$first,
      block:{number:$bn},
      orderBy: totalValueLockedUSD,
      orderDirection: desc
    ){
      token0 { symbol }
      token1 { symbol }
      tick
    }
  }`;
  const d = await gqlFetch<{ pools: Pool[] }>(QUICK_V3_ID, q, { bn, first });
  return d.pools;
}

export async function fetchQuickSwapV3Snapshot(secondsAgo = 0, first = 300) {
  const current = await getCurrentBlock();
  const bn = secondsAgo === 0 ? current : current - Math.floor(secondsAgo / AVG_BLOCK_TIME);

  const [maticUSD, pools] = await Promise.all([
    basePriceUSD(bn),
    topPools(bn, first),
  ]);

  // Try derivedMatic first, then fallback to derivedUSD
  let tokensUSD: { symbol: string; priceUSD: number }[] = [];
  try {
    const tokens = await topTokensDerivedMatic(bn, first);
    tokensUSD = tokens
      .map(t => ({
        symbol: t.symbol,
        priceUSD: (t.derivedMatic ? Number(t.derivedMatic) : 0) * maticUSD,
      }))
      .filter(t => t.symbol && t.priceUSD > 0);
  } catch {
    const tokens = await topTokensDerivedUSD(bn, first);
    tokensUSD = tokens
      .map(t => ({
        symbol: t.symbol,
        priceUSD: t.derivedUSD ? Number(t.derivedUSD) : 0,
      }))
      .filter(t => t.symbol && t.priceUSD > 0);
  }

  const poolsData = pools.map(p => ({
    pair: `${p.token0.symbol}/${p.token1.symbol}`,
    tick: Number(p.tick),
  }));

  return { blockNumber: bn, secondsAgo, tokens: tokensUSD, pools: poolsData };
}
