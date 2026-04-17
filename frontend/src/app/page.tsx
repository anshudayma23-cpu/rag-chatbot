'use client';

import { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message } from '@/types';
import { sendMessage, getHistory, clearHistory, exportChat } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import WelcomeScreen from '@/components/WelcomeScreen';
import ChatArea from '@/components/ChatArea';
import InputArea from '@/components/InputArea';

export default function Home() {
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  // Initialize session
  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('rag_session_id') : null;
    if (stored) {
      setSessionId(stored);
    } else {
      const newId = uuidv4();
      setSessionId(newId);
      localStorage.setItem('rag_session_id', newId);
    }
  }, []);

  // Load history when session changes
  useEffect(() => {
    if (!sessionId) return;
    
    const loadHistory = async () => {
      try {
        const data = await getHistory(sessionId);
        if (data.history && data.history.length > 0) {
          setMessages(data.history.map((msg: any) => ({
            ...msg,
            id: msg.timestamp || uuidv4(),
          })));
          setHasStarted(true);
        }
      } catch (err) {
        console.log('No history to load');
      }
    };
    
    loadHistory();
  }, [sessionId]);

  const handleSendMessage = useCallback(async (content: string) => {
    if (!sessionId || !content.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setHasStarted(true);

    try {
      const response = await sendMessage(sessionId, content.trim());
      
      // Determine message type from response
      let type: Message['type'] = 'factual';
      const responseLower = response.response.toLowerCase();
      
      if (responseLower.includes('cannot provide') || responseLower.includes('not authorized') || response.intent === 'ADVISORY') {
        type = 'refusal';
      } else if (responseLower.includes('error')) {
        type = 'error';
      }

      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        type,
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        type: 'error',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const handleNewChat = useCallback(() => {
    const newId = uuidv4();
    setSessionId(newId);
    localStorage.setItem('rag_session_id', newId);
    setMessages([]);
    setHasStarted(false);
  }, []);

  const handleClearChat = useCallback(async () => {
    if (!confirm('Are you sure you want to clear this conversation?')) return;
    
    try {
      await clearHistory(sessionId);
      setMessages([]);
      setHasStarted(false);
      
      const newId = uuidv4();
      setSessionId(newId);
      localStorage.setItem('rag_session_id', newId);
    } catch (error) {
      alert('Failed to clear conversation');
    }
  }, [sessionId]);

  const handleExportChat = useCallback(async () => {
    try {
      const result = await exportChat(sessionId, 'markdown');
      alert(`Chat exported successfully!\nFile: ${result.filepath}`);
    } catch (error) {
      alert('Failed to export chat');
    }
  }, [sessionId]);

  const handleQuickAction = useCallback((query: string) => {
    handleSendMessage(query);
  }, [handleSendMessage]);

  return (
    <div className="flex h-screen w-screen bg-slate-50">
      <Sidebar
        sessionId={sessionId}
        onNewChat={handleNewChat}
        onClearChat={handleClearChat}
        onExportChat={handleExportChat}
        onQuickAction={handleQuickAction}
      />
      
      <main className="flex-1 flex flex-col min-w-0">
        <Header />
        
        {!hasStarted ? (
          <WelcomeScreen onSuggestionClick={handleSendMessage} />
        ) : (
          <ChatArea messages={messages} isLoading={isLoading} />
        )}
        
        <InputArea onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>
    </div>
  );
}
