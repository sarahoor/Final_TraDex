"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { formatPrice } from "@/lib/format";

export type MarketRow = {
  symbol: string;
  price: number | null; // median
  byProtocol: Record<string, number | undefined>; // { uni?: number; sushi?: number; quick?: number; cake?: number }
};

const protoOrder: Array<keyof MarketRow["byProtocol"]> = ["uni", "sushi", "quick", "cake"];
const protoName: Record<string, string> = { uni: "Uniswap", sushi: "Sushiswap", quick: "QuickSwap", cake: "Pancake" };
const protoBadge: Record<string, string> = {
  uni: "bg-indigo-500/10 text-indigo-600 border-indigo-500/30",
  sushi: "bg-rose-500/10 text-rose-600 border-rose-500/30",
  quick: "bg-purple-500/10 text-purple-600 border-purple-500/30",
  cake: "bg-amber-500/10 text-amber-700 border-amber-500/30",
};

export default function MarketTable({ rows, loading }: { rows: MarketRow[]; loading: boolean }) {
  const [sortKey, setSortKey] = useState<"symbol" | "price">("symbol");
  const [dir, setDir] = useState<1 | -1>(1);
  const router = useRouter();

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      if (sortKey === "symbol") return a.symbol.localeCompare(b.symbol) * dir;
      const av = a.price ?? -Infinity,
        bv = b.price ?? -Infinity;
      return (av - bv) * dir;
    });
    return copy;
  }, [rows, sortKey, dir]);

  const Th = ({ label, keyName }: { label: "symbol" | "price"; keyName: "symbol" | "price" }) => (
    <th
      className="text-left text-xs font-semibold px-3 py-2 cursor-pointer select-none"
      onClick={() => {
        if (sortKey === keyName) setDir(d => (d === 1 ? -1 : 1));
        else {
          setSortKey(keyName);
          setDir(keyName === "symbol" ? 1 : -1);
        }
      }}
      title="Click to sort"
    >
      {label === "symbol" ? "Symbol" : "Median (USD)"} {sortKey === keyName ? (dir === 1 ? "▲" : "▼") : ""}
    </th>
  );

  const onRowClick = (sym: string) => router.push(`/token/${sym.toLowerCase()}?interval=1h&days=30`);

  return (
    <div className="card overflow-hidden">
      <table className="table">
        <thead>
          <tr>
            <Th label="symbol" keyName="symbol" />
            <Th label="price" keyName="price" />
            {protoOrder.map(p => (
              <th key={p} className="text-left text-xs font-semibold px-3 py-2">
                <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 ${protoBadge[p]}`}>
                  {protoName[p]}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td className="px-3 py-4" colSpan={2 + protoOrder.length}>
                Loading…
              </td>
            </tr>
          ) : sorted.length === 0 ? (
            <tr>
              <td className="px-3 py-4" colSpan={2 + protoOrder.length}>
                No results
              </td>
            </tr>
          ) : (
            sorted.map(r => (
              <tr key={r.symbol} className="row-hover" onClick={() => onRowClick(r.symbol)}>
                <td className="px-3 py-2 font-medium">{r.symbol}</td>
                <td className="px-3 py-2 tabular-nums">{formatPrice(r.price)}</td>
                {protoOrder.map(p => (
                  <td key={p} className="px-3 py-2 tabular-nums text-xs">
                    {formatPrice(r.byProtocol[p])}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
