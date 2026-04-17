'use client';

import { SuggestionCard } from '@/types';

interface WelcomeScreenProps {
  onSuggestionClick: (query: string) => void;
}

const suggestions: SuggestionCard[] = [
  {
    id: '1',
    icon: '💰',
    title: 'What is the NAV of HDFC Small Cap Fund?',
    query: 'What is the NAV of HDFC Small Cap Fund?',
  },
  {
    id: '2',
    icon: '⚠️',
    title: 'Compare HDFC Defence and Multi Cap',
    query: 'Compare HDFC Defence and HDFC Multi Cap Fund',
    note: '(Will refuse - no comparisons)',
  },
  {
    id: '3',
    icon: '💳',
    title: 'What is the minimum SIP amount?',
    query: 'What is the minimum SIP for HDFC Nifty 50 Index Fund?',
  },
];

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="px-8 py-12 max-w-3xl">
      <h1 className="text-3xl font-semibold text-slate-900 mb-2">
        Welcome back, Investor.
      </h1>
      <p className="text-slate-500 mb-8">
        I'm ready to answer factual questions about HDFC Mutual Funds.
      </p>

      <div className="grid grid-cols-3 gap-4">
        {suggestions.map((card) => (
          <button
            key={card.id}
            onClick={() => onSuggestionClick(card.query)}
            className="text-left p-6 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-blue-500 hover:shadow-md hover:-translate-y-0.5 transition-all"
          >
            <div className="w-11 h-11 bg-slate-100 rounded-xl flex items-center justify-center text-2xl mb-4">
              {card.icon}
            </div>
            <p className="text-sm font-medium text-slate-800 leading-relaxed">
              &ldquo;{card.title}&rdquo;
            </p>
            {card.note && (
              <p className="text-xs text-amber-600 mt-2">{card.note}</p>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
