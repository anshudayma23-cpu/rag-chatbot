'use client';

import { useState } from 'react';
import { Send } from 'lucide-react';

interface InputAreaProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function InputArea({ onSendMessage, isLoading }: InputAreaProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const charCount = input.length;
  const isOverLimit = charCount > 500;

  return (
    <div className="px-8 py-6 bg-white border-t border-slate-200">
      <form onSubmit={handleSubmit} className="max-w-3xl">
        <div 
          className={`flex items-center gap-3 bg-slate-50 rounded-2xl border-2 px-4 py-3 transition-colors ${
            isOverLimit ? 'border-red-400' : 'border-slate-200 focus-within:border-blue-500'
          }`}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about HDFC Mutual Funds..."
            className="flex-1 bg-transparent border-none outline-none text-slate-800 placeholder:text-slate-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || isOverLimit}
            className="w-11 h-11 bg-blue-500 text-white rounded-xl flex items-center justify-center hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
        
        <div className="flex justify-between items-center mt-3 px-1">
          <span className="text-xs text-slate-400">
            FundBot provides factual information only. Not investment advice.
          </span>
          <span className={`text-xs font-medium ${isOverLimit ? 'text-red-500' : 'text-slate-400'}`}>
            {charCount}/500
          </span>
        </div>
      </form>
    </div>
  );
}
