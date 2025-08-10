"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import IntervalTabs from "./IntervalTabs";
import { type Interval, useCandles } from "@/hooks/useCandles";
import * as L from "lightweight-charts";

type ChartKind = "candle" | "area";

// Tune this if the chart feels too tall/short vs. header+controls
const VIEWPORT_OFFSET_PX = 160;

export default function PriceChart({ symbol: rawSymbol }: { symbol: string }) {
  const symbol = (rawSymbol || "").toUpperCase();
  const [interval, setInterval] = useState<Interval>("1h");
  const [days, setDays] = useState<number>(30);
  const [kind, setKind] = useState<ChartKind>("candle");

  const { candles, isLoading } = useCandles(symbol, interval, days);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<L.IChartApi | null>(null);
  const seriesRef = useRef<L.ISeriesApi<"Candlestick"> | L.ISeriesApi<"Area"> | null>(null);
  const destroyed = useRef(false);

  // Build chart once; keep it resized
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    destroyed.current = false;

    const ensureChart = () => {
      if (destroyed.current || chartRef.current) return;
      const chart = L.createChart(el, {
        width: el.clientWidth || window.innerWidth,
        height: el.clientHeight || Math.max(320, window.innerHeight - VIEWPORT_OFFSET_PX),
        layout: { background: { color: "transparent" }, textColor: "var(--color-base-content)" },
        rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.1, bottom: 0.2 } },
        timeScale: {
          borderVisible: false,
          timeVisible: true,
          secondsVisible: interval === "1m" || interval === "5m",
        },
        grid: {
          horzLines: { color: "rgba(128,128,128,0.10)" },
          vertLines: { color: "rgba(128,128,128,0.06)" },
        },
        crosshair: { mode: 1 },
      });
      chartRef.current = chart;
    };

    const ro = new ResizeObserver(() => {
      if (destroyed.current) return;
      const el2 = containerRef.current;
      const chart = chartRef.current;
      if (!el2) return;
      if (!chart) {
        ensureChart();
        return;
      }
      chart.applyOptions({ width: el2.clientWidth, height: el2.clientHeight });
    });

    ensureChart();
    ro.observe(el);

    return () => {
      destroyed.current = true;
      ro.disconnect();
      try {
        if (chartRef.current && seriesRef.current) {
          chartRef.current.removeSeries(seriesRef.current);
        }
      } catch {}
      seriesRef.current = null;
      try {
        chartRef.current?.remove();
      } catch {}
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep secondsVisible synced with interval
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    chart.applyOptions({ timeScale: { secondsVisible: interval === "1m" || interval === "5m" } });
  }, [interval]);

  // Create/replace series when kind changes — with strict guards
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || destroyed.current) return;

    if (seriesRef.current) {
      try {
        chart.removeSeries(seriesRef.current);
      } catch {}
      seriesRef.current = null;
    }

    try {
      seriesRef.current =
        kind === "candle"
          ? chart.addSeries(L.CandlestickSeries, {
              upColor: "#16a34a",
              downColor: "#ef4444",
              borderVisible: false,
              wickUpColor: "#16a34a",
              wickDownColor: "#ef4444",
            } as any)
          : chart.addSeries(L.AreaSeries, {
              lineWidth: 2,
              priceLineVisible: false,
              lastValueVisible: true,
              crosshairMarkerVisible: true,
            } as any);
    } catch {
      // If chart was torn down mid-flight, just ignore
      seriesRef.current = null;
    }
  }, [kind]);

  // Prepare data
  const dataCandles = useMemo(
    () =>
      candles.map(c => ({
        time: c.time as L.Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    [candles],
  );

  const dataArea = useMemo(
    () =>
      candles.map(c => ({
        time: c.time as L.Time,
        value: c.close,
      })),
    [candles],
  );

  // Push data (guard everything)
  useEffect(() => {
    if (destroyed.current) return;
    const chart = chartRef.current;
    const s = seriesRef.current as any;
    if (!chart || !s || candles.length === 0) return;

    try {
      if (kind === "candle") {
        s.setData(dataCandles as L.SeriesDataItemTypeMap["Candlestick"]);
      } else {
        s.setData(dataArea as L.SeriesDataItemTypeMap["Area"]);
      }
      chart.timeScale().fitContent();
    } catch {
      // ignore if chart/series disappeared during route changes
    }
  }, [candles, dataCandles, dataArea, kind]);

  // Label
  const isAddress = /^0x[a-f0-9]{40}$/i.test(symbol);
  const displayLabel = isAddress ? `${symbol.slice(0, 6)}…${symbol.slice(-4)}` : symbol;

  return (
    <div className="card w-full">
      <div className="card-body w-full">
        {/* header */}
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <div className="text-lg font-semibold">{displayLabel}</div>
            <span className="chip">History: Binance → CoinGecko</span>
          </div>
        </div>

        {/* chart + bottom controls */}
        <div className="w-full h-[calc(100vh-160px)] flex flex-col">
          <div ref={containerRef} className="flex-1 w-full" />
          <div className="mt-3 flex items-center justify-between">
            <IntervalTabs
              value={interval}
              onChange={(i, d) => {
                setInterval(i);
                setDays(d);
              }}
            />
            <div className="inline-flex rounded-xl border overflow-hidden">
              <button
                className={`px-3 py-1.5 text-sm ${kind === "candle" ? "bg-base-200" : ""}`}
                onClick={() => setKind("candle")}
              >
                Candle
              </button>
              <button
                className={`px-3 py-1.5 text-sm ${kind === "area" ? "bg-base-200" : ""}`}
                onClick={() => setKind("area")}
              >
                Area
              </button>
            </div>
          </div>
        </div>

        {isLoading && <div className="mt-2 text-xs opacity-60">Loading…</div>}
      </div>
    </div>
  );
}
