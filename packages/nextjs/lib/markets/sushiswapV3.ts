import { AVG_BLOCK_TIME, gqlFetch } from './thegraph';

const SUSHI_V3_ID = '5nnoU1nUFeWqtXgbpC54L9PWdpgo7Y9HYinR3uTMsfzs';

type Bundle = { ethPriceUSD: string };
type Token = { symbol: string; derivedETH: string };
type PoolToken = { symbol: string };
type Pool = { token0: PoolToken; token1: PoolToken; tick: string };

async function getCurrentBlock(): Promise<number> {
  const q = `{ _meta { block { number } } }`;
  const d = await gqlFetch<{ _meta: { block: { number: number } } }>(SUSHI_V3_ID, q);
  return d._meta.block.number;
}

async function basePrice(bn: number): Promise<number> {
  const q = `query($bn:Int!){ bundles(first:1, block:{number:$bn}){ ethPriceUSD } }`;
  const d = await gqlFetch<{ bundles: Bundle[] }>(SUSHI_V3_ID, q, { bn });
  return Number(d.bundles[0].ethPriceUSD);
}

async function topTokens(bn: number, first = 300): Promise<Token[]> {
  const q = `query($bn:Int!,$first:Int!){
    tokens(first:$first, block:{number:$bn}){ symbol derivedETH }
  }`;
  const d = await gqlFetch<{ tokens: Token[] }>(SUSHI_V3_ID, q, { bn, first });
  return d.tokens;
}

async function topPools(bn: number, first = 300): Promise<Pool[]> {
  const q = `query($bn:Int!,$first:Int!){
    pools(first:$first, block:{number:$bn}){ token0{symbol} token1{symbol} tick }
  }`;
  const d = await gqlFetch<{ pools: Pool[] }>(SUSHI_V3_ID, q, { bn, first });
  return d.pools;
}

export async function fetchSushiswapV3Snapshot(secondsAgo = 0, first = 300) {
  const current = await getCurrentBlock();
  const bn = secondsAgo === 0 ? current : current - Math.floor(secondsAgo / AVG_BLOCK_TIME);

  const [ethUSD, tokens, pools] = await Promise.all([
    basePrice(bn),
    topTokens(bn, first),
    topPools(bn, first),
  ]);

  const tokenPrices = tokens
    .map(t => ({ symbol: t.symbol, priceUSD: Number(t.derivedETH) * ethUSD }))
    .filter(t => t.symbol && t.priceUSD > 0);

  const poolsData = pools.map(p => ({
    pair: `${p.token0.symbol}/${p.token1.symbol}`,
    tick: Number(p.tick),
  }));

  return { blockNumber: bn, secondsAgo, tokens: tokenPrices, pools: poolsData };
}
