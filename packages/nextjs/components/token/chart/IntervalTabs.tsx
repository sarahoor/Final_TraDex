'use client';
import React from 'react';
import type { Interval } from '@/hooks/useCandles';

const items: { key: Interval; label: string; days: number }[] = [
  { key: '1m',  label: '1m',  days: 1 },
  { key: '5m',  label: '5m',  days: 2 },
  { key: '30m', label: '30m', days: 7 },
  { key: '1h',  label: '1h',  days: 30 },
  { key: '1d',  label: '1d',  days: 365 },
];

export default function IntervalTabs({
  value, onChange,
}: {
  value: Interval;
  onChange: (i: Interval, days: number) => void;
}) {
  return (
    <div className="inline-flex rounded-xl border overflow-hidden">
      {items.map(it => (
        <button
          key={it.key}
          onClick={() => onChange(it.key, it.days)}
          className={`px-3 py-1.5 text-sm ${value === it.key ? 'bg-primary text-primary-content' : 'bg-base-100 hover:bg-base-200'}`}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}
