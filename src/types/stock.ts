import { Time } from 'lightweight-charts';

export interface CandleData {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface MonteCarloScenario {
  current_price: number;
  days_ahead: number;
  scenarios: {
    p10_support: number[];
    p50_median: number[];
    p90_optimistic: number[];
  };
  metrics: {
    expected_return_p50_pct: number;
    max_risk_p10_pct: number;
    max_gain_p90_pct: number;
    annualized_volatility_pct: number;
  };
}

export interface StockDetailPayload {
  symbol: string;
  updated_at: string;
  signal: {
    upward_probability_10d: number;
    bias_rating: 'Bullish' | 'Bearish' | 'Neutral';
  };
  monteCarlo: MonteCarloScenario;
  candles: CandleData[];
}