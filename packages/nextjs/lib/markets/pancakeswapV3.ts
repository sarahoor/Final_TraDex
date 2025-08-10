import { AVG_BLOCK_TIME, gqlFetch } from './thegraph';

// PancakeSwap v3 (BNB Chain) subgraph id
const PANCAKE_V3_ID = 'A1fvJWQLBeUAggX2WQTMm3FKjXTekNXo77ZySun4YN2m';

type Bundle = { ethPriceUSD: string }; // schema shows ethPriceUSD field (BNB price in USD here)
type Token = { symbol: string; derivedETH: string };
type PoolToken = { symbol: string };
type Pool = { token0: PoolToken; token1: PoolToken; tick: string };

async function getCurrentBlock(): Promise<number> {
  const q = `{ _meta { block { number } } }`;
  const d = await gqlFetch<{ _meta: { block: { number: number } } }>(PANCAKE_V3_ID, q);
  return d._meta.block.number;
}

async function basePriceUSD(bn: number): Promise<number> {
  const q = `query($bn:Int!){ bundles(first:1, block:{number:$bn}){ ethPriceUSD } }`;
  const d = await gqlFetch<{ bundles: Bundle[] }>(PANCAKE_V3_ID, q, { bn });
  return Number(d.bundles[0].ethPriceUSD);
}

async function topTokens(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    tokens(
      first:$first,
      block:{number:$bn},
      orderBy: totalValueLockedUSD,
      orderDirection: desc
    ){ symbol derivedETH }
  }`;
  return (await gqlFetch<{ tokens: Token[] }>(PANCAKE_V3_ID, q, { bn, first })).tokens;
}

async function topPools(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    pools(
      first:$first,
      block:{number:$bn},
      orderBy: totalValueLockedUSD,
      orderDirection: desc
    ){ token0{symbol} token1{symbol} tick }
  }`;
  return (await gqlFetch<{ pools: Pool[] }>(PANCAKE_V3_ID, q, { bn, first })).pools;
}

export async function fetchPancakeV3Snapshot(secondsAgo = 0, first = 300) {
  const current = await getCurrentBlock();
  const bn = secondsAgo === 0 ? current : current - Math.floor(secondsAgo / AVG_BLOCK_TIME);

  const [baseUSD, tokens, pools] = await Promise.all([
    basePriceUSD(bn),
    topTokens(bn, first),
    topPools(bn, first),
  ]);

  const tokenPrices = tokens
    .map(t => ({ symbol: t.symbol, priceUSD: Number(t.derivedETH) * baseUSD }))
    .filter(t => t.symbol && t.priceUSD > 0);

  const poolsData = pools.map(p => ({
    pair: `${p.token0.symbol}/${p.token1.symbol}`,
    tick: Number(p.tick),
  }));

  return { blockNumber: bn, secondsAgo, tokens: tokenPrices, pools: poolsData };
}
