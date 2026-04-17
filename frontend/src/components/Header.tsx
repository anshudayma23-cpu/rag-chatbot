'use client';

import { HelpCircle } from 'lucide-react';

export default function Header() {
  return (
    <header className="flex items-center justify-between px-8 py-4 bg-white border-b border-slate-200">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Mutual Fund Assistant</h2>
        <div className="flex items-center gap-2 mt-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm text-slate-500">Facts-Only Mode</span>
        </div>
      </div>
      
      <button
        className="w-9 h-9 rounded-full border border-slate-200 flex items-center justify-center text-slate-500 hover:border-blue-500 hover:text-blue-500 transition-colors"
        title="Help"
      >
        <HelpCircle size={18} />
      </button>
    </header>
  );
}
