import { AVG_BLOCK_TIME, gqlFetch } from './thegraph';

const UNI_V3_ID = '5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV';

type Bundle = { ethPriceUSD: string };
type Token = { symbol: string; derivedETH: string };
type PoolToken = { symbol: string };
type Pool = { token0: PoolToken; token1: PoolToken; tick: string };

async function getCurrentBlock(): Promise<number> {
  const q = `{ _meta { block { number } } }`;
  const d = await gqlFetch<{ _meta: { block: { number: number } } }>(UNI_V3_ID, q);
  return d._meta.block.number;
}
async function basePrice(bn: number): Promise<number> {
  const q = `query($bn:Int!){ bundles(first:1, block:{number:$bn}){ ethPriceUSD } }`;
  const d = await gqlFetch<{ bundles: Bundle[] }>(UNI_V3_ID, q, { bn });
  return Number(d.bundles[0].ethPriceUSD);
}
async function allTokens(bn: number): Promise<Token[]> {
  const out: Token[] = []; const first = 1000; let skip = 0;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const q = `query($bn:Int!,$first:Int!,$skip:Int!){
      tokens(first:$first, skip:$skip, block:{number:$bn}){ symbol derivedETH }
    }`;
    const d = await gqlFetch<{ tokens: Token[] }>(UNI_V3_ID, q, { bn, first, skip });
    if (!d.tokens.length) break; out.push(...d.tokens); skip += first;
  }
  return out;
}
async function allPools(bn: number): Promise<Pool[]> {
  const out: Pool[] = []; const first = 1000; let skip = 0;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const q = `query($bn:Int!,$first:Int!,$skip:Int!){
      pools(first:$first, skip:$skip, block:{number:$bn}){ token0{symbol} token1{symbol} tick }
    }`;
    const d = await gqlFetch<{ pools: Pool[] }>(UNI_V3_ID, q, { bn, first, skip });
    if (!d.pools.length) break; out.push(...d.pools); skip += first;
  }
  return out;
}

// add optional `first` param and remove deep pagination
export async function fetchUniswapV3Snapshot(secondsAgo = 0, first = 300) {
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
    pair: `${p.token0.symbol}/${p.token1.symbol}`, tick: Number(p.tick)
  }));
  return { blockNumber: bn, secondsAgo, tokens: tokenPrices, pools: poolsData };
}

async function topTokens(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    tokens(
      first: $first
      block: { number: $bn }
      orderBy: totalValueLockedUSD
      orderDirection: desc
      where: { derivedETH_not: null, derivedETH_gt: 0, symbol_not: "" }
    ) {
      symbol
      derivedETH
      totalValueLockedUSD
    }
  }`;
  const d = await gqlFetch<{ tokens: { symbol: string; derivedETH: string }[] }>(UNI_V3_ID, q, { bn, first });
  return d.tokens;
}


async function topPools(bn: number, first = 300) {
  const q = `query($bn:Int!,$first:Int!){
    pools(first:$first, block:{number:$bn}){ token0{symbol} token1{symbol} tick }
  }`;
  const d = await gqlFetch<{ pools: { token0:{symbol:string}, token1:{symbol:string}, tick:string }[] }>(UNI_V3_ID, q, { bn, first });
  return d.pools;
}

