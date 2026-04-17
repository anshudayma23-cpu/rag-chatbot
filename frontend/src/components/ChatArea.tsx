'use client';

import { useEffect, useRef } from 'react';
import { Message } from '@/types';
import MessageBubble from './MessageBubble';

interface ChatAreaProps {
  messages: Message[];
  isLoading: boolean;
}

export default function ChatArea({ messages, isLoading }: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <div className="max-w-3xl flex flex-col gap-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex gap-4">
            <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-sm">
              🤖
            </div>
            <div className="bg-slate-100 rounded-2xl rounded-bl-sm px-5 py-4">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce-delay-1" />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce-delay-2" />
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce-delay-3" />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
