import type { UTCTimestamp } from 'lightweight-charts';

export type OHLC = {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

export type History = OHLC[];
