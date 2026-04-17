'use client';

import { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  const getMessageStyles = () => {
    if (isUser) {
      return 'bg-blue-500 text-white rounded-2xl rounded-br-sm';
    }
    
    switch (message.type) {
      case 'refusal':
        return 'bg-amber-50 border-l-4 border-amber-400 text-amber-900 rounded-2xl rounded-bl-sm';
      case 'error':
        return 'bg-red-50 border-l-4 border-red-400 text-red-900 rounded-2xl rounded-bl-sm';
      case 'factual':
        return 'bg-emerald-50 border-l-4 border-emerald-400 text-slate-800 rounded-2xl rounded-bl-sm';
      default:
        return 'bg-slate-100 text-slate-800 rounded-2xl rounded-bl-sm';
    }
  };

  const formatContent = (content: string) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />');
  };

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''} animate-fade-in`}>
      {/* Avatar */}
      <div 
        className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-slate-200 text-slate-600'
        }`}
      >
        {isUser ? '🙂' : '🤖'}
      </div>

      {/* Message Content */}
      <div className={`max-w-[80%] shadow-sm ${getMessageStyles()}`}>
        <div 
          className="px-5 py-3.5 text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
        />
      </div>
    </div>
  );
}
