'use client';

import useSWR from 'swr';
import type { History } from '@/types/market';
import { genMock } from '@/lib/token/mock';
import { fromCoinGecko } from '@/lib/token/coingecko';
import { fromBinance } from '@/lib/token/binance';
import { mergeHistories } from '@/lib/token/merge';

export function useCoinHistory(
  symbol: string,
  vs = 'usd',
  days = 30,
  interval = '1h',
  useMock = false
) {
  return useSWR<History>(
    ['coin-history', symbol, vs, days, interval, useMock],
    async () => {
      if (useMock) return genMock(symbol, days, interval);

      const [cg, bin] = await Promise.allSettled([
        fromCoinGecko(symbol, vs, days),
        fromBinance(symbol, interval),
      ]);

      const take = <T,>(r: PromiseSettledResult<T>): T =>
        r.status === 'fulfilled' ? r.value : (([] as unknown) as T);

      return mergeHistories([take(cg), take(bin)]);
    },
    { revalidateOnFocus: false }
  );
}
