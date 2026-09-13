'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { getActiveOpportunities, getOverviewStats, ArbitrageOpportunity } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import OpportunityCard from '@/components/OpportunityCard';
import Header from '@/components/Header';
import { Activity, DollarSign, TrendingUp, BarChart3 } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

interface DashboardFilters {
  minProfitPercent: number;
  minVolumeUsd: number;
  maxVolumeUsd: number;
  maxCommissionPercent: number;
  selectedSymbols: string[];
  blacklist: string[];
  whitelist: string[];
}

const DEFAULT_FILTERS: DashboardFilters = {
  minProfitPercent: 0,
  minVolumeUsd: 0,
  maxVolumeUsd: 1000000,
  maxCommissionPercent: 100,
  selectedSymbols: [],
  blacklist: [],
  whitelist: [],
};

export default function Home() {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);
  const [filtersLoaded, setFiltersLoaded] = useState(false);
  
  const { isConnected, newOpportunities, goneOpportunityIds } = useWebSocket();
  
  // Загрузка фильтров из localStorage — вызывается при монтировании и по storage events
  useEffect(() => {
    const loadFilters = () => {
      const savedFilters = localStorage.getItem('dashboard_filters');
      if (savedFilters) {
        try {
          const parsed = JSON.parse(savedFilters);
          setFilters(prev => ({ ...prev, ...parsed }));
        } catch (e) {
          console.error('Failed to load filters:', e);
        }
      } else {
        localStorage.setItem('dashboard_filters', JSON.stringify(DEFAULT_FILTERS));
      }
      setFiltersLoaded(true);
    };

    loadFilters();
    window.addEventListener('storage', loadFilters);
    return () => window.removeEventListener('storage', loadFilters);
  }, []);
  
  const fetchData = useCallback(async () => {
    try {
      const [opps] = await Promise.all([
        getActiveOpportunities(200),
        getOverviewStats(),
      ]);
      setOpportunities(opps);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);
  
  // Фильтрация возможностей
  const filteredOpportunities = useMemo(() => {
    if (!filtersLoaded) return opportunities;
    
    let filtered = [...opportunities];
    
    if (filters.minProfitPercent > 0) {
      filtered = filtered.filter(opp => opp.net_profit_percent >= filters.minProfitPercent);
    }
    
    if (filters.minVolumeUsd > 0) {
      filtered = filtered.filter(opp => opp.volume_usd >= filters.minVolumeUsd);
    }
    
    if (filters.maxVolumeUsd < 1000000) {
      filtered = filtered.filter(opp => opp.volume_usd <= filters.maxVolumeUsd);
    }
    
    if (filters.maxCommissionPercent < 100) {
      filtered = filtered.filter(opp => opp.total_fee_percent <= filters.maxCommissionPercent);
    }
    
    if (filters.selectedSymbols.length > 0) {
      filtered = filtered.filter(opp => filters.selectedSymbols.includes(opp.symbol));
    }
    
    if (filters.blacklist.length > 0) {
      filtered = filtered.filter(opp => !filters.blacklist.includes(opp.symbol));
    }
    
    if (filters.whitelist.length > 0) {
      filtered = filtered.filter(opp => filters.whitelist.includes(opp.symbol));
    }
    
    filtered.sort((a, b) => b.net_profit_percent - a.net_profit_percent);
    
    return filtered;
  }, [opportunities, filters, filtersLoaded]);
  
  // Статистика
  const filteredStats = useMemo(() => {
    const totalProfit = filteredOpportunities.reduce((sum, opp) => sum + opp.net_profit_usd, 0);
    const avgProfit = filteredOpportunities.length > 0 
      ? filteredOpportunities.reduce((sum, opp) => sum + opp.net_profit_percent, 0) / filteredOpportunities.length 
      : 0;
    const maxProfit = filteredOpportunities.length > 0 
      ? Math.max(...filteredOpportunities.map(opp => opp.net_profit_usd)) 
      : 0;
    
    return { totalProfit, avgProfit, maxProfit };
  }, [filteredOpportunities]);
  
  // WebSocket — новые возможности
  useEffect(() => {
    if (newOpportunities.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setOpportunities(prev => [...newOpportunities, ...prev].slice(0, 200));
      toast.success(`🎯 Новая возможность! ${newOpportunities[0]?.symbol}`);
    }
  }, [newOpportunities]);
  
  // WebSocket — ушедшие возможности
  useEffect(() => {
    if (goneOpportunityIds.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setOpportunities(prev => prev.filter(opp => !goneOpportunityIds.includes(opp.id)));
    }
  }, [goneOpportunityIds]);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }
  
  const hasActiveFilters = 
    filters.minProfitPercent > 0 ||
    filters.minVolumeUsd > 0 ||
    filters.maxVolumeUsd < 1000000 ||
    filters.maxCommissionPercent < 100 ||
    filters.selectedSymbols.length > 0 ||
    filters.blacklist.length > 0 ||
    filters.whitelist.length > 0;
  
  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster />
      <Header lastUpdate={lastUpdate} isConnected={isConnected} />
      
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Активных арбитражей</p>
                <p className="text-2xl font-bold">{filteredOpportunities.length}</p>
                {opportunities.length > filteredOpportunities.length && (
                  <p className="text-xs text-gray-400">Всего: {opportunities.length}</p>
                )}
              </div>
              <Activity className="text-blue-500" size={32} />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Общая прибыль</p>
                <p className="text-2xl font-bold text-green-600">
                  ${filteredStats.totalProfit.toFixed(2)}
                </p>
              </div>
              <DollarSign className="text-yellow-500" size={32} />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Средняя прибыль</p>
                <p className="text-2xl font-bold">{filteredStats.avgProfit.toFixed(2)}%</p>
              </div>
              <TrendingUp className="text-purple-500" size={32} />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Макс. прибыль</p>
                <p className="text-2xl font-bold text-green-600">
                  ${filteredStats.maxProfit.toFixed(2)}
                </p>
              </div>
              <BarChart3 className="text-gray-500" size={32} />
            </div>
          </div>
        </div>
        
        {hasActiveFilters && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-700 flex justify-between items-center">
            <span>🔍 Применены фильтры. Показано {filteredOpportunities.length} из {opportunities.length} возможностей.</span>
            <a href="/settings" className="text-blue-600 hover:underline">⚙️ Изменить фильтры</a>
          </div>
        )}
        
        <div>
          <h2 className="text-xl font-semibold mb-4">
            🔥 Активные возможности ({filteredOpportunities.length})
          </h2>
          {filteredOpportunities.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              🤔 Нет активных арбитражных возможностей
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredOpportunities.map((opp) => (
                <OpportunityCard key={opp.id} opportunity={opp} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}