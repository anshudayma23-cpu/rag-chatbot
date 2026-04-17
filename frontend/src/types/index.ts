export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type?: 'factual' | 'refusal' | 'error' | 'greeting';
}

export interface ChatResponse {
  response: string;
  intent: string;
  enhanced_query?: string;
  source_count?: number;
  warning?: string;
}

export interface HistoryResponse {
  session_id: string;
  history: Message[];
  message_count: number;
}

export interface SuggestionCard {
  id: string;
  icon: string;
  title: string;
  query: string;
  note?: string;
}

export interface NavItem {
  id: string;
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick?: () => void;
}
