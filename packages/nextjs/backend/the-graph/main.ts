import 'dotenv/config';
import { fetchUniswapV3 } from "./uniswapV3.js";
import { fetchSushiswapV3 } from "./sushiswapV3.js";

async function main(secondAgo: number): Promise<void> {
  try {
    await fetchUniswapV3(secondAgo);
    await fetchSushiswapV3(secondAgo);
    console.log("All data fetched and saved successfully!");
  } catch (e) {
    console.error("Central error:", e);
  }
}