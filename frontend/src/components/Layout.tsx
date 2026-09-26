import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: 'Explore', path: '/' },
    { name: 'Quest', path: '/quest' },
    { name: 'History', path: '/history' },
    { name: 'MIX', path: '/mix' },
    { name: 'LOCK-IN', path: '/lockin' },
    { name: 'Profile', path: '/profile' },
  ];

  return (
    <div className="min-h-screen bg-surface flex flex-col font-body-md text-on-surface dark">
      <header className="fixed top-0 left-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
        <div className="h-20 max-w-7xl mx-auto px-6 lg:px-12 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4 shrink-0">
            <div className="w-8 h-8 rounded bg-primary-container text-on-primary-container flex items-center justify-center font-bold">SQ</div>
            <div className="flex flex-col">
              <span className="font-headline-sm text-headline-sm tracking-tight text-on-surface uppercase">SKILL QUEST</span>
              <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant">Weekend Discovery</span>
            </div>
          </div>
          
          <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-low">
            <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse"></span>
            <span className="font-label-md text-label-md text-on-surface-variant">Connected • New Horizon Ready</span>
          </div>

          <nav className="hidden md:flex items-center gap-1 rounded-xl p-1 bg-surface-container-lowest">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path || (item.path === '/quest' && location.pathname.startsWith('/quest'));
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={cn(
                    "px-4 py-2 rounded-lg transition-all",
                    isActive 
                      ? "text-on-surface font-semibold bg-surface-container"
                      : "font-label-lg text-label-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container"
                  )}
                >
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3 shrink-0">
            <div className="hidden sm:flex flex-col items-end">
              <span className="font-label-lg text-label-lg text-on-surface">{user?.username || 'Explorer'}</span>
              <span className="font-label-sm text-label-sm text-tertiary uppercase cursor-pointer" onClick={logout}>Sign Out</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center text-on-surface uppercase font-bold">
              {user?.username?.charAt(0) || 'U'}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile nav */}
      <nav className="md:hidden fixed bottom-0 w-full z-50 bg-surface/90 backdrop-blur-xl border-t border-surface-container flex">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || (item.path === '/quest' && location.pathname.startsWith('/quest'));
          return (
            <Link
              key={item.name}
              to={item.path}
              className={cn(
                "flex-1 py-4 text-center font-label-md transition-all",
                isActive ? "text-primary bg-surface-container-low" : "text-on-surface-variant"
              )}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>

      <main className="w-full pt-20 flex-1 flex flex-col pb-20 md:pb-0">
        <Outlet />
      </main>

      <footer className="w-full bg-surface-container-lowest py-10 shadow-[0_1px_8px_rgba(0,0,0,0.04)] hidden md:block">
        <div className="max-w-7xl mx-auto px-6 lg:px-12 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="font-headline-sm text-headline-sm text-on-surface uppercase">SKILL QUEST</span>
            <span className="font-body-sm text-body-sm text-on-surface-variant">• Exploratory Cartography Engine</span>
          </div>
          <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
            © 2026 SKILL QUEST INC. SYSTEM HORIZON ARCHITECTURE.
          </div>
        </div>
      </footer>
    </div>
  );
};
