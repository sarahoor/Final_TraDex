"use client";

import React, { useMemo, useState } from "react";
import MarketTable from "@/components/markets/MarketTable";
import ProtocolToggle from "@/components/markets/ProtocolToggle";
import StatCards from "@/components/markets/StatCards";
import { useUnifiedPrices } from "@/hooks/useUnifiedPrices";

export default function MarketDashboard() {
  const [enabled, setEnabled] = useState({ uni: false, sushi: true, quick: true, cake: true });
  const [query, setQuery] = useState("");
  const [secondsAgo, setSecondsAgo] = useState(0);

  const { data, isLoading, error } = useUnifiedPrices({ secondsAgo, enabled, first: 300, refreshMs: 60_000 });

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toUpperCase();
    if (!q) return data.rows;
    return data.rows.filter(r => r.symbol.includes(q));
  }, [data, query]);

  return (
    <main className="p-6 space-y-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Markets Dashboard</h1>
          <p className="opacity-70 text-sm">Live token prices</p>
        </div>
        <div className="flex gap-3 items-center">
          <ProtocolToggle enabled={enabled} onChange={setEnabled} />
          <input
            className="border rounded-xl px-3 py-2 text-sm w-56"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search symbol…"
          />
          <select
            className="border rounded-xl px-3 py-2 text-sm"
            value={secondsAgo}
            onChange={e => setSecondsAgo(Number(e.target.value))}
          >
            <option value={0}>Now</option>
            <option value={3600}>1 hour ago</option>
            <option value={21600}>6 hours ago</option>
            <option value={86400}>1 day ago</option>
          </select>
        </div>
      </header>

      <StatCards data={data} loading={isLoading} />

      {error ? (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-700">
          Failed to load: {String(error)}
        </div>
      ) : (
        <>
          <MarketTable rows={filtered} loading={isLoading} />
          {/* Simple pairs list */}
          <section className="space-y-2">
            <h2 className="section-title">Top Pairs</h2>
            <div className="grid grid-auto-fit gap-2">
              {(data?.pairs || []).slice(0, 24).map((p, i) => (
                <div key={i} className="card">
                  <div className="card-body py-3">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{p.pair}</div>
                      <div className="chip">tick: {p.tick}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
