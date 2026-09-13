'use client';

import { useEffect, useState } from 'react';
import { getOpportunityHistory, ArbitrageOpportunity } from '@/lib/api';
import OpportunityCard from '@/components/OpportunityCard';
import Header from '@/components/Header';

export default function HistoryPage() {
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState({ symbol: '', buyExchange: '', sellExchange: '' });
  
  const perPage = 20;
  
  useEffect(() => {
    let cancelled = false;

    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await getOpportunityHistory(page, perPage, filter.symbol, filter.buyExchange, filter.sellExchange);
        if (!cancelled) {
          setOpportunities(data.opportunities);
          setTotal(data.total);
        }
      } catch (error) {
        if (!cancelled) console.error('Failed to fetch history:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();
    return () => { cancelled = true; };
  }, [page, filter]);
  
  const totalPages = Math.ceil(total / perPage);
  
  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Символ (BTC/USDT)"
              value={filter.symbol}
              onChange={(e) => setFilter({ ...filter, symbol: e.target.value })}
              className="border rounded-lg px-3 py-2"
            />
            <input
              type="text"
              placeholder="Биржа покупки"
              value={filter.buyExchange}
              onChange={(e) => setFilter({ ...filter, buyExchange: e.target.value })}
              className="border rounded-lg px-3 py-2"
            />
            <input
              type="text"
              placeholder="Биржа продажи"
              value={filter.sellExchange}
              onChange={(e) => setFilter({ ...filter, sellExchange: e.target.value })}
              className="border rounded-lg px-3 py-2"
            />
            <button
              onClick={() => setPage(1)}
              className="bg-blue-500 text-white rounded-lg px-4 py-2 hover:bg-blue-600"
            >
              Применить фильтр
            </button>
          </div>
        </div>
        
        {/* Results */}
        {loading ? (
          <div className="text-center py-8">Загрузка...</div>
        ) : opportunities.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
            Нет записей
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {opportunities.map((opp) => (
                <OpportunityCard key={opp.id} opportunity={opp} />
              ))}
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-6">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50"
                >
                  ← Назад
                </button>
                <span className="px-4 py-2">
                  Страница {page} из {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border rounded-lg disabled:opacity-50"
                >
                  Вперед →
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}