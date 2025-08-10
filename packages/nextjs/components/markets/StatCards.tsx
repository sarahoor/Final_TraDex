"use client";

import React, { useMemo } from "react";
import type { UnifiedData } from "@/hooks/useUnifiedPrices";

export default function StatCards({ data, loading }: { data: UnifiedData | undefined; loading: boolean }) {
  const stats = useMemo(() => {
    if (!data) return { count: 0, median: 0, max: 0, min: 0 };
    const prices = data.rows.map(r => r.price).filter((x): x is number => typeof x === "number");
    const count = prices.length;
    if (count === 0) return { count: 0, median: 0, max: 0, min: 0 };
    const sorted = [...prices].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    const max = sorted[sorted.length - 1];
    const min = sorted[0];
    return { count, median, max, min };
  }, [data]);

  const Card = ({ title, value }: { title: string; value: number | string }) => (
    <div className="flex-1 rounded-2xl border p-4">
      <div className="text-xs opacity-70">{title}</div>
      <div className="text-xl font-semibold mt-1">
        {typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 6 }) : value}
      </div>
    </div>
  );

  return (
    <section className="grid grid-cols-1 md:grid-cols-4 gap-3">
      <Card title="Tokens (with price)" value={loading ? "…" : stats.count} />
      <Card title="Median Price" value={loading ? "…" : stats.median} />
      <Card title="Max Price" value={loading ? "…" : stats.max} />
      <Card title="Min Price" value={loading ? "…" : stats.min} />
    </section>
  );
}
