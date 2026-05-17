/**
 * TypeScript types for query functionality
 */

export interface Source {
  type: 'code' | 'documentation';
  file_path?: string;
  line_start?: number;
  line_end?: number;
  content: string;
  relevance_score: number;
  documentation_id?: string;
  documentation_title?: string;
}

export interface Query {
  question: string;
  repository_id?: string;
  session_id?: string;
  max_results?: number;
  include_code?: boolean;
  include_docs?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  confidence_score: number;
  response_time_ms: number;
  session_id: string;
  related_questions: string[];
}

export interface QueryFeedback {
  query_id: string;
  feedback: -1 | 0 | 1;
  comment?: string;
}

export interface SearchQuery {
  query: string;
  repository_id?: string;
  search_type?: 'semantic' | 'keyword' | 'hybrid';
  limit?: number;
  filters?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  type: 'code' | 'documentation';
  title: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
  highlights: string[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  confidence_score?: number;
  related_questions?: string[];
  timestamp: Date;
}

export interface StreamEvent {
  type: 'start' | 'status' | 'sources' | 'chunk' | 'answer' | 'done' | 'error';
  message?: string;
  content?: string;
  data?: any;
}

export interface QueryStats {
  total_queries: number;
  avg_response_time_ms: number;
  positive_feedback: number;
  negative_feedback: number;
  neutral_feedback: number;
}

// Made with Bob