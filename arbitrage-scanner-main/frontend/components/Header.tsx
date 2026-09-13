'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface HeaderProps {
  lastUpdate?: Date;
  isConnected?: boolean;
}

export default function Header({ lastUpdate, isConnected }: HeaderProps) {
  const pathname = usePathname();
  
  const navItems = [
    { href: '/', label: 'Дашборд', icon: '📊' },
    { href: '/history', label: 'История', icon: '📜' },
    { href: '/settings', label: 'Настройки', icon: '⚙️' },
  ];
  
  return (
    <header className="bg-white shadow-sm sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-3">
          {/* Logo */}
          <div>
            <h1 className="text-2xl font-bold text-blue-600">🚀 Arbitrage Scanner</h1>
            {lastUpdate && (
              <p className="text-sm text-gray-500 hidden md:block">
                Обновлено: {lastUpdate.toLocaleTimeString()} | 
                WebSocket: {isConnected ? '🟢 Online' : '🔴 Offline'}
              </p>
            )}
          </div>
          
          {/* Navigation */}
          <nav className="flex gap-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-4 py-2 rounded-lg transition flex items-center gap-1 ${
                    isActive
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
        
        {/* Mobile status */}
        {lastUpdate && (
          <p className="text-xs text-gray-500 mt-2 md:hidden text-center">
            Обновлено: {lastUpdate.toLocaleTimeString()} | 
            WebSocket: {isConnected ? '🟢 Online' : '🔴 Offline'}
          </p>
        )}
      </div>
    </header>
  );
}