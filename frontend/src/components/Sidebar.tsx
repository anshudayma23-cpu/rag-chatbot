'use client';

import { MessageSquare, Trash2, Download, Shield } from 'lucide-react';

interface SidebarProps {
  sessionId: string;
  onNewChat: () => void;
  onClearChat: () => void;
  onExportChat: () => void;
  onQuickAction: (query: string) => void;
}

const quickActions = [
  { label: 'NAV Query', query: 'What is the NAV of HDFC Small Cap Fund?' },
  { label: 'Expense Ratio', query: 'What is the expense ratio of HDFC Defence Fund?' },
  { label: 'Fund Manager', query: 'Who manages HDFC Multi Cap Fund?' },
  { label: 'Exit Load', query: 'What is the exit load for HDFC Mid Cap Fund?' },
];

export default function Sidebar({
  sessionId,
  onNewChat,
  onClearChat,
  onExportChat,
  onQuickAction,
}: SidebarProps) {
  return (
    <aside className="w-72 bg-[#1a1a2e] flex flex-col h-full flex-shrink-0">
      {/* Header */}
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white text-xl font-bold">
            📊
          </div>
          <span className="text-white text-xl font-semibold">FundBot</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 flex flex-col gap-1">
        <button
          onClick={onNewChat}
          className="flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
        >
          <MessageSquare size={18} />
          <span className="text-sm font-medium">New Chat</span>
        </button>
        
        <button
          onClick={onClearChat}
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors"
        >
          <Trash2 size={18} />
          <span className="text-sm">Clear History</span>
        </button>
        
        <button
          onClick={onExportChat}
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors"
        >
          <Download size={18} />
          <span className="text-sm">Export Chat</span>
        </button>
      </nav>

      {/* Quick Actions */}
      <div className="px-5 py-4 flex-1">
        <h4 className="text-xs font-medium text-white/50 uppercase tracking-wider mb-3">
          Quick Actions
        </h4>
        <div className="flex flex-col gap-2">
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => onQuickAction(action.query)}
              className="text-left px-3 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white/80 text-sm hover:bg-white/10 hover:border-blue-500/50 transition-all"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/15 text-emerald-400 text-xs font-medium mb-3">
          <Shield size={14} />
          <span>SEBI Compliant</span>
        </div>
        <p className="text-white/40 text-xs font-mono">
          Session: {sessionId.slice(0, 8)}...
        </p>
      </div>
    </aside>
  );
}
