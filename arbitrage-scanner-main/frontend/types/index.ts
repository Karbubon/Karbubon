export interface ArbitrageOpportunity {
  id: number;
  symbol: string;
  base_asset: string;
  quote_asset: string;
  buy_exchange: string;
  sell_exchange: string;
  buy_price: number;
  sell_price: number;
  min_buy_price: number | null;
  max_buy_price: number | null;
  min_sell_price: number | null;
  max_sell_price: number | null;
  volume_asset: number;
  volume_usd: number;
  buy_orders_used: number;
  sell_orders_used: number;
  buy_fee_percent: number;
  sell_fee_percent: number;
  buy_fee_usd: number;
  sell_fee_usd: number;
  transfer_fee_usd: number;
  total_fee_usd: number;
  total_fee_percent: number;
  gross_spread_percent: number;
  net_spread_percent: number;
  gross_profit_usd: number;
  net_profit_usd: number;
  net_profit_percent: number;
  network: string | null;
  buy_trade_url: string | null;
  sell_trade_url: string | null;
  is_active: boolean;
  detected_at: string;
  updated_at: string | null;
  disappeared_at: string | null;
}

export interface StatsResponse {
  total_opportunities: number;
  active_opportunities: number;
  total_profit_usd: number;
  avg_profit_percent: number;
  max_profit_usd: number;
  best_opportunity: ArbitrageOpportunity | null;
  exchanges_count: number;
  pairs_monitored: number;
  scanner_uptime_seconds: number | null;
}

export interface DailyStats {
  date: string;
  count: number;
  total_profit_usd: number;
  avg_profit_percent: number;
}

export interface Setting {
  key: string;
  value: string | number | boolean | null;
  description: string | null;
}
