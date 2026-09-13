'use client';

import { ArbitrageOpportunity } from '@/lib/api';
import { getCMCInfo, CMCInfo } from '@/lib/api';
import { ExternalLink, Ban, CheckCircle, Info } from 'lucide-react';
import { useState, useEffect } from 'react';

interface OpportunityCardProps {
  opportunity: ArbitrageOpportunity;
  isNew?: boolean;
}

export default function OpportunityCard({ opportunity, isNew }: OpportunityCardProps) {
  const [isBlacklisted, setIsBlacklisted] = useState(false);
  const [isWhitelisted, setIsWhitelisted] = useState(false);
  const [cmcInfo, setCmcInfo] = useState<CMCInfo | null>(null);
  const [showCmcInfo, setShowCmcInfo] = useState(false);
  const [loadingCmc, setLoadingCmc] = useState(false);
  
  const profitColor = opportunity.net_profit_usd > 0 ? 'text-green-600' : 'text-red-600';
  const profitBg = opportunity.net_profit_usd > 0 ? 'bg-green-50' : 'bg-red-50';
  
  const formatPrice = (price: number) => {
    if (price < 0.01) return price.toFixed(8);
    if (price < 1) return price.toFixed(6);
    return price.toFixed(2);
  };
  
  const formatNumber = (num: number) => {
    if (num > 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num > 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num > 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toFixed(2);
  };
  
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };
  
  // Загрузка данных из CoinMarketCap
  useEffect(() => {
    const loadCMCInfo = async () => {
      setLoadingCmc(true);
      try {
        const data = await getCMCInfo(opportunity.symbol);
        setCmcInfo(data);
      } catch (error) {
        console.error('Failed to load CMC info:', error);
      } finally {
        setLoadingCmc(false);
      }
    };
    
    loadCMCInfo();
  }, [opportunity.symbol]);
  
  // Добавление в черный список
  const addToBlacklist = () => {
    const savedFilters = localStorage.getItem('dashboard_filters');
    if (savedFilters) {
      const filters = JSON.parse(savedFilters);
      const blacklist = filters.blacklist || [];
      if (!blacklist.includes(opportunity.symbol)) {
        const newBlacklist = [...blacklist, opportunity.symbol];
        const newFilters = { ...filters, blacklist: newBlacklist };
        localStorage.setItem('dashboard_filters', JSON.stringify(newFilters));
        setIsBlacklisted(true);
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'dashboard_filters',
          newValue: JSON.stringify(newFilters)
        }));
        alert(`✅ ${opportunity.symbol} добавлен в черный список`);
      }
    }
  };
  
  // Добавление в белый список
  const addToWhitelist = () => {
    const savedFilters = localStorage.getItem('dashboard_filters');
    if (savedFilters) {
      const filters = JSON.parse(savedFilters);
      const whitelist = filters.whitelist || [];
      if (!whitelist.includes(opportunity.symbol)) {
        const newWhitelist = [...whitelist, opportunity.symbol];
        const newFilters = { ...filters, whitelist: newWhitelist };
        localStorage.setItem('dashboard_filters', JSON.stringify(newFilters));
        setIsWhitelisted(true);
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'dashboard_filters',
          newValue: JSON.stringify(newFilters)
        }));
        alert(`✅ ${opportunity.symbol} добавлен в белый список`);
      }
    }
  };
  
  // Расчет суммы продажи
  const sellAmountUsd = opportunity.volume_usd + opportunity.net_profit_usd;
  
  return (
    <div className={`bg-white rounded-lg shadow-md p-4 border-l-4 ${isNew ? 'border-green-500 animate-pulse' : 'border-blue-500'}`}>
      {/* Заголовок с кнопками */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-lg font-bold">{opportunity.symbol}</h3>
          <div className="flex gap-1">
            <button 
              onClick={addToBlacklist}
              className={`p-1 rounded transition ${isBlacklisted ? 'bg-gray-100 text-gray-400' : 'hover:bg-red-50 text-red-500'}`}
              title="Добавить в черный список"
            >
              <Ban size={16} />
            </button>
            <button 
              onClick={addToWhitelist}
              className={`p-1 rounded transition ${isWhitelisted ? 'bg-gray-100 text-gray-400' : 'hover:bg-green-50 text-green-500'}`}
              title="Добавить в белый список"
            >
              <CheckCircle size={16} />
            </button>
            {(cmcInfo || loadingCmc) && (
              <button 
                onClick={() => setShowCmcInfo(!showCmcInfo)}
                className="p-1 rounded hover:bg-gray-100 text-gray-500 transition"
                title="Информация о монете"
              >
                <Info size={16} />
              </button>
            )}
          </div>
        </div>
        <div className={`${profitBg} ${profitColor} px-3 py-1 rounded-full font-bold text-sm whitespace-nowrap ml-2`}>
          +${opportunity.net_profit_usd.toFixed(2)} ({opportunity.net_profit_percent.toFixed(3)}%)
        </div>
      </div>
      
      {/* Биржи - ВОССТАНОВЛЕННЫЙ БЛОК */}
      <div className="text-sm text-gray-500 mb-3">
        {opportunity.buy_exchange} → {opportunity.sell_exchange}
      </div>
      
      {/* CMC Информация */}
      {showCmcInfo && (
        <div className="mb-3 p-2 bg-gray-50 rounded-lg text-xs">
          {loadingCmc ? (
            <div className="text-center text-gray-400">Загрузка данных CMC...</div>
          ) : cmcInfo ? (
            <div className="flex justify-between items-center">
              <div>
                <span className="font-medium">{cmcInfo.name}</span>
                <span className="text-gray-500 ml-2">#{cmcInfo.rank}</span>
                <div className="text-gray-500">
                  {cmcInfo.percent_change_24h > 0 ? (
                    <span className="text-green-500">+{cmcInfo.percent_change_24h.toFixed(2)}%</span>
                  ) : (
                    <span className="text-red-500">{cmcInfo.percent_change_24h.toFixed(2)}%</span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div>💰 ${formatNumber(cmcInfo.price_usd)}</div>
                <div className="text-gray-500">MCap: ${formatNumber(cmcInfo.market_cap)}</div>
                <div className="text-gray-500 text-xs">24h Vol: ${formatNumber(cmcInfo.volume_24h)}</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400">Нет данных CMC</div>
          )}
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
        <div>
          <div className="text-gray-500 text-xs">Покупка</div>
          <div className="font-mono">{formatPrice(opportunity.buy_price)}</div>
          <div className="text-xs text-gray-400">
            {formatNumber(opportunity.volume_asset)} {opportunity.base_asset} 
            ({opportunity.buy_orders_used} орд.)
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-xs">Продажа</div>
          <div className="font-mono">{formatPrice(opportunity.sell_price)}</div>
          <div className="text-xs text-gray-400">
            {formatNumber(opportunity.volume_asset)} {opportunity.base_asset} 
            ({opportunity.sell_orders_used} орд.)
          </div>
        </div>
      </div>
      
      {/* Суммы в USD */}
      <div className="flex justify-between items-center mb-3 p-2 bg-gray-50 rounded-lg">
        <div>
          <div className="text-xs text-gray-500">💸 Купить на</div>
          <div className="font-bold text-red-600">${opportunity.volume_usd.toFixed(2)}</div>
        </div>
        <div className="text-gray-400 text-xl">→</div>
        <div>
          <div className="text-xs text-gray-500">💰 Продать на</div>
          <div className="font-bold text-green-600">${sellAmountUsd.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500">📈 Прибыль</div>
          <div className="font-bold text-green-600">+${opportunity.net_profit_usd.toFixed(2)}</div>
        </div>
      </div>
      
      <div className="flex justify-between items-center text-xs text-gray-500">
        <div className="flex gap-2">
          {opportunity.network && (
            <span className="bg-gray-100 px-2 py-1 rounded">🌐 {opportunity.network}</span>
          )}
          <span>📊 {(opportunity.total_fee_percent * 100).toFixed(2)}% комиссия</span>
        </div>
        <div className="flex gap-2">
          {opportunity.buy_trade_url && (
            <a href={opportunity.buy_trade_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline flex items-center gap-1">
              Buy <ExternalLink size={12} />
            </a>
          )}
          {opportunity.sell_trade_url && (
            <a href={opportunity.sell_trade_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline flex items-center gap-1">
              Sell <ExternalLink size={12} />
            </a>
          )}
        </div>
      </div>
      
      <div className="mt-2 text-xs text-gray-400 flex justify-between">
        <span>{formatTime(opportunity.detected_at)}</span>
        {opportunity.is_active && <span className="text-green-500">● активен</span>}
      </div>
    </div>
  );
}