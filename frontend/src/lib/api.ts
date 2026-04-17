import axios from 'axios';
import { ChatResponse, HistoryResponse } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function sendMessage(
  sessionId: string,
  message: string
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat', {
    session_id: sessionId,
    message,
  });
  return response.data;
}

export async function getHistory(
  sessionId: string,
  limit: number = 50
): Promise<HistoryResponse> {
  const response = await api.get<HistoryResponse>('/history', {
    params: { session_id: sessionId, limit },
  });
  return response.data;
}

export async function clearHistory(sessionId: string): Promise<void> {
  await api.post('/clear', { session_id: sessionId });
}

export async function exportChat(
  sessionId: string,
  format: 'markdown' | 'json' = 'markdown'
): Promise<{ filepath: string; message: string }> {
  const response = await api.get('/export', {
    params: { session_id: sessionId, format },
  });
  return response.data;
}
