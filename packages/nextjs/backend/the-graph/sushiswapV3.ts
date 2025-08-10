import fetch from "node-fetch";
import fs from "fs/promises";

const API_KEY = process.env.ABI_KEY;
const SUBGRAPH_URL = `https://gateway.thegraph.com/api/${API_KEY}/subgraphs/id/5nnoU1nUFeWqtXgbpC54L9PWdpgo7Y9HYinR3uTMsfzs`;

// Average block time ~12 seconds
const AVG_BLOCK_TIME = 12;

interface GraphResponse<T> {
  data: T;
  errors?: any;
}

interface Bundle {
  ethPriceUSD: string;
}

interface Token {
  symbol: string;
  derivedETH: string;
}

interface PoolToken {
  symbol: string;
}

interface Pool {
  token0: PoolToken;
  token1: PoolToken;
  tick: string;
}

async function getCurrentBlock(): Promise<number> {
  const query = `
  {
    _meta {
      block {
        number
      }
    }
  }`;

  const res = await fetch(SUBGRAPH_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  const json = (await res.json()) as GraphResponse<{ _meta: { block: { number: number } } }>;
  if (json.errors) throw new Error(JSON.stringify(json.errors));

  return json.data._meta.block.number;
}

async function fetchBasePrice(blockNumber: number): Promise<number> {
  const query = `
  {
    bundles(first: 1, block: {number: ${blockNumber}}) {
      ethPriceUSD
    }
  }`;
  const res = await fetch(SUBGRAPH_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  const json = (await res.json()) as GraphResponse<{ bundles: Bundle[] }>;
  if (json.errors) throw new Error(JSON.stringify(json.errors));
  return Number(json.data.bundles[0].ethPriceUSD);
}

async function fetchTokens(blockNumber: number): Promise<Token[]> {
  const tokens: Token[] = [];
  const pageSize = 1000;
  let skip = 0;

  while (true) {
    const query = `
    {
      tokens(first: ${pageSize}, skip: ${skip}, block: {number: ${blockNumber}}) {
        symbol
        derivedETH
      }
    }`;
    const res = await fetch(SUBGRAPH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const json = (await res.json()) as GraphResponse<{ tokens: Token[] }>;
    if (json.errors) throw new Error(JSON.stringify(json.errors));

    if (json.data.tokens.length === 0) break;

    tokens.push(...json.data.tokens);
    skip += pageSize;
  }
  return tokens;
}

async function fetchPools(blockNumber: number): Promise<Pool[]> {
  const pools: Pool[] = [];
  const pageSize = 1000;
  let skip = 0;

  while (true) {
    const query = `
    {
      pools(first: ${pageSize}, skip: ${skip}, block: {number: ${blockNumber}}) {
        token0 {
          symbol
        }
        token1 {
          symbol
        }
        tick
      }
    }`;
    const res = await fetch(SUBGRAPH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const json = (await res.json()) as GraphResponse<{ pools: Pool[] }>;
    if (json.errors) throw new Error(JSON.stringify(json.errors));

    if (json.data.pools.length === 0) break;

    pools.push(...json.data.pools);
    skip += pageSize;
  }
  return pools;
}

export async function fetchSushiswapV3(timeAgoSeconds: number): Promise<void> {
  // calculate blocks ago from input seconds
  const blocksAgo = Math.floor(timeAgoSeconds / 12);

  const currentBlock = await getCurrentBlock();
  const blockToQuery = timeAgoSeconds === 0 ? currentBlock : currentBlock - blocksAgo;

  console.log(`Fetching Sushiswap V3 prices from ${timeAgoSeconds} seconds ago...`);
  console.log(`Using block number: ${blockToQuery}`);

  const ethPriceUSD = await fetchBasePrice(blockToQuery);
  const tokens = await fetchTokens(blockToQuery);
  const pools = await fetchPools(blockToQuery);

  const tokenPrices = tokens
    .map(t => ({
      symbol: t.symbol,
      priceUSD: Number(t.derivedETH) * ethPriceUSD,
    }))
    .filter(t => t.priceUSD > 0);

  const poolsData = pools.map(p => ({
    pair: `${p.token0.symbol}/${p.token1.symbol}`,
    tick: Number(p.tick),
  }));

  const output = {
    tokens: tokenPrices,
    pools: poolsData,
  };

  await fs.writeFile("sushiswapV3_prices_and_pools.json", JSON.stringify(output, null, 2));
  console.log("Saved Sushiswap V3 prices and pools");
}