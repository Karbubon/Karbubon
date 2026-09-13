'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import toast, { Toaster } from 'react-hot-toast';
import { RefreshCw, Plus, Trash2, Save } from 'lucide-react';

interface DashboardFilters {
  minProfitPercent: number;
  minVolumeUsd: number;
  maxVolumeUsd: number;
  maxCommissionPercent: number;
  selectedSymbols: string[];
  blacklist: string[];
  whitelist: string[];
}

// Значения по умолчанию (минимальные фильтры - показываем всё)
const DEFAULT_FILTERS: DashboardFilters = {
  minProfitPercent: 0,
  minVolumeUsd: 0,
  maxVolumeUsd: 1000000,
  maxCommissionPercent: 100,
  selectedSymbols: [],
  blacklist: [],
  whitelist: [],
};

function loadFilters(): DashboardFilters {
  if (typeof window === 'undefined') return DEFAULT_FILTERS;
  try {
    const saved = localStorage.getItem('dashboard_filters');
    if (saved) return { ...DEFAULT_FILTERS, ...JSON.parse(saved) };
  } catch { /* ignore */ }
  return DEFAULT_FILTERS;
}

export default function SettingsPage() {
  const [filters, setFilters] = useState<DashboardFilters>(loadFilters);
  const [blacklistInput, setBlacklistInput] = useState('');
  const [whitelistInput, setWhitelistInput] = useState('');
  const [symbolInput, setSymbolInput] = useState('');
  const [allSymbols, setAllSymbols] = useState<string[]>([]);
  
  
  // Загрузка списка символов из API
  useEffect(() => {
    fetch('http://localhost:8000/api/opportunities/active?limit=200')
      .then(res => res.json())
      .then((data: Array<{ symbol: string }>) => {
        const symbols = [...new Set(data.map(opp => opp.symbol))];
        setAllSymbols(symbols);
      })
      .catch(console.error);
  }, []);
  
  // Сохранение настроек
  const saveSettings = () => {
    localStorage.setItem('dashboard_filters', JSON.stringify(filters));
    toast.success('Настройки сохранены');
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'dashboard_filters',
      newValue: JSON.stringify(filters)
    }));
  };
  
  // Полный сброс настроек до значений по умолчанию
  const resetSettings = () => {
    setFilters(DEFAULT_FILTERS);
    localStorage.setItem('dashboard_filters', JSON.stringify(DEFAULT_FILTERS));
    toast.success('Настройки сброшены до значений по умолчанию');
    
    // Отправляем событие для обновления дашборда
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'dashboard_filters',
      newValue: JSON.stringify(DEFAULT_FILTERS)
    }));
  };
  
  // Управление символами
  const addSymbol = () => {
    if (symbolInput && !filters.selectedSymbols.includes(symbolInput.toUpperCase())) {
      setFilters({
        ...filters,
        selectedSymbols: [...filters.selectedSymbols, symbolInput.toUpperCase()]
      });
      setSymbolInput('');
    }
  };
  
  const removeSymbol = (symbol: string) => {
    setFilters({
      ...filters,
      selectedSymbols: filters.selectedSymbols.filter(s => s !== symbol)
    });
  };
  
  // Черный список
  const addToBlacklist = () => {
    if (blacklistInput && !filters.blacklist.includes(blacklistInput.toUpperCase())) {
      setFilters({
        ...filters,
        blacklist: [...filters.blacklist, blacklistInput.toUpperCase()],
        whitelist: filters.whitelist.filter(s => s !== blacklistInput.toUpperCase())
      });
      setBlacklistInput('');
    }
  };
  
  const removeFromBlacklist = (item: string) => {
    setFilters({
      ...filters,
      blacklist: filters.blacklist.filter(s => s !== item)
    });
  };
  
  // Белый список
  const addToWhitelist = () => {
    if (whitelistInput && !filters.whitelist.includes(whitelistInput.toUpperCase())) {
      setFilters({
        ...filters,
        whitelist: [...filters.whitelist, whitelistInput.toUpperCase()],
        blacklist: filters.blacklist.filter(s => s !== whitelistInput.toUpperCase())
      });
      setWhitelistInput('');
    }
  };
  
  const removeFromWhitelist = (item: string) => {
    setFilters({
      ...filters,
      whitelist: filters.whitelist.filter(s => s !== item)
    });
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <Toaster />
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">⚙️ Настройки дашборда</h1>
          <div className="flex gap-2">
            <button
              onClick={resetSettings}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition flex items-center gap-2"
            >
              <RefreshCw size={18} />
              Сбросить всё
            </button>
            <button
              onClick={saveSettings}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition flex items-center gap-2"
            >
              <Save size={18} />
              Сохранить
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Основные параметры */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              Фильтры
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Минимальная прибыль (%)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={filters.minProfitPercent}
                  onChange={(e) => setFilters({ ...filters, minProfitPercent: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">0 = показывать все</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Минимальный объем ($)
                </label>
                <input
                  type="number"
                  step="50"
                  value={filters.minVolumeUsd}
                  onChange={(e) => setFilters({ ...filters, minVolumeUsd: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">0 = без ограничений</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Максимальный объем ($)
                </label>
                <input
                  type="number"
                  step="100"
                  value={filters.maxVolumeUsd}
                  onChange={(e) => setFilters({ ...filters, maxVolumeUsd: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">Большое число = без ограничений</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Максимальная комиссия (%)
                </label>
                <input
                  type="number"
                  step="0.05"
                  value={filters.maxCommissionPercent}
                  onChange={(e) => setFilters({ ...filters, maxCommissionPercent: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">100 = без ограничений</p>
              </div>
            </div>
          </div>
          
          {/* Выбранные символы */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
              Выбранные символы
            </h2>
            
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Например: BTC/USDT"
                value={symbolInput}
                onChange={(e) => setSymbolInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
                list="symbols-list"
                className="flex-1 border rounded-lg px-3 py-2"
              />
              <button
                onClick={addSymbol}
                className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition"
              >
                <Plus size={20} />
              </button>
            </div>
            <datalist id="symbols-list">
              {allSymbols.map(s => <option key={s} value={s} />)}
            </datalist>
            
            <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
              {filters.selectedSymbols.length === 0 ? (
                <p className="text-gray-500 text-sm">Все символы</p>
              ) : (
                filters.selectedSymbols.map(s => (
                  <span key={s} className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-sm flex items-center gap-1">
                    {s}
                    <button onClick={() => removeSymbol(s)} className="hover:text-purple-600">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                ))
              )}
            </div>
          </div>
          
          {/* Черный список */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              Черный список (исключить)
            </h2>
            
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Например: BTC/USDT"
                value={blacklistInput}
                onChange={(e) => setBlacklistInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addToBlacklist()}
                className="flex-1 border rounded-lg px-3 py-2"
              />
              <button
                onClick={addToBlacklist}
                className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition"
              >
                <Plus size={20} />
              </button>
            </div>
            
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {filters.blacklist.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Черный список пуст</p>
              ) : (
                filters.blacklist.map((item: string) => (
                  <div key={item} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span className="font-mono">{item}</span>
                    <button onClick={() => removeFromBlacklist(item)} className="text-red-500 hover:text-red-700">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Белый список */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              Белый список (только эти)
            </h2>
            
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Например: BTC/USDT"
                value={whitelistInput}
                onChange={(e) => setWhitelistInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addToWhitelist()}
                className="flex-1 border rounded-lg px-3 py-2"
              />
              <button
                onClick={addToWhitelist}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition"
              >
                <Plus size={20} />
              </button>
            </div>
            
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {filters.whitelist.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Белый список пуст</p>
              ) : (
                filters.whitelist.map((item: string) => (
                  <div key={item} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span className="font-mono">{item}</span>
                    <button onClick={() => removeFromWhitelist(item)} className="text-red-500 hover:text-red-700">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              )}
            </div>
            {filters.whitelist.length > 0 && (
              <p className="text-xs text-amber-600 mt-2">
                ⚠️ Активен - показываются только указанные пары
              </p>
            )}
          </div>
        </div>
        
        <div className="mt-6 bg-blue-50 rounded-lg p-4 text-sm text-blue-700">
          <h3 className="font-semibold mb-1">ℹ️ Информация</h3>
          <p>Значения по умолчанию показывают ВСЕ возможности (без фильтрации).</p>
          <p className="mt-1">Чтобы увидеть все 7 карточек, установите: прибыль = 0%, объем мин = 0, комиссия = 100%.</p>
        </div>
      </main>
    </div>
  );
}