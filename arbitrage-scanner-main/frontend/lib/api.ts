import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Существующие типы
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

// Добавляем тип Setting
export interface Setting {
  key: string;
  value: string | number | boolean | null;
  description: string | null;
}

export interface CMCInfo {
  symbol: string;
  base_asset: string;
  name: string;
  rank: number;
  price_usd: number;
  market_cap: number;
  volume_24h: number;
  percent_change_24h: number;
}


// API методы

export const getCMCInfo = async (symbol: string): Promise<CMCInfo> => {
  // Извлекаем только базовый актив (например, из SOL/USDT -> SOL)
  const baseAsset = symbol.split('/')[0];
  const response = await api.get(`/cmc/${baseAsset}`);
  return response.data;
};

export const getTopCoins = async (limit: number = 50): Promise<CMCInfo[]> => {
  const response = await api.get(`/cmc/top/${limit}`);
  return response.data;
};

export const getActiveOpportunities = async (limit: number = 50): Promise<ArbitrageOpportunity[]> => {
  const response = await api.get('/opportunities/active', { params: { limit } });
  return response.data;
};

export const getOpportunityHistory = async (
  page: number = 1,
  perPage: number = 50,
  symbol?: string,
  buyExchange?: string,
  sellExchange?: string
): Promise<{ total: number; page: number; per_page: number; opportunities: ArbitrageOpportunity[] }> => {
  const params: Record<string, string | number> = { page, per_page: perPage };
  if (symbol) params.symbol = symbol;
  if (buyExchange) params.buy_exchange = buyExchange;
  if (sellExchange) params.sell_exchange = sellExchange;
  const response = await api.get('/opportunities/history', { params });
  return response.data;
};

export const getOpportunityById = async (id: number): Promise<ArbitrageOpportunity> => {
  const response = await api.get(`/opportunities/${id}`);
  return response.data;
};

export const getOverviewStats = async (): Promise<StatsResponse> => {
  const response = await api.get('/stats/overview');
  return response.data;
};

export const getDailyStats = async (days: number = 7): Promise<DailyStats[]> => {
  const response = await api.get('/stats/daily', { params: { days } });
  return response.data;
};

export const getSettings = async (): Promise<Setting[]> => {
  const response = await api.get('/settings/');
  return response.data;
};

export const updateSetting = async (key: string, value: string | number | boolean | null): Promise<Setting> => {
  // Используем PUT вместо POST (или оставляем POST, зависит от бэкенда)
  const response = await api.put(`/settings/${key}`, { value });
  return response.data;
};

export default api;