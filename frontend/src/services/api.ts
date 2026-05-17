/**
 * API service for communicating with the backend
 */

import {
  Query,
  QueryResponse,
  QueryFeedback,
  SearchQuery,
  SearchResult,
  QueryStats,
  StreamEvent
} from '../types/query';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Ask a question (non-streaming)
   */
  async askQuestion(query: Query): Promise<QueryResponse> {
    const response = await fetch(`${this.baseUrl}/api/query/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get answer');
    }

    return response.json();
  }

  /**
   * Ask a question with streaming response
   */
  async *streamQuestion(query: Query): AsyncGenerator<StreamEvent, void, unknown> {
    const response = await fetch(`${this.baseUrl}/api/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });

    if (!response.ok) {
      throw new Error('Failed to start stream');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              return;
            }

            try {
              const event: StreamEvent = JSON.parse(data);
              yield event;
            } catch (e) {
              console.error('Failed to parse event:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Perform hybrid search
   */
  async search(searchQuery: SearchQuery): Promise<SearchResult[]> {
    const response = await fetch(`${this.baseUrl}/api/query/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchQuery),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Search failed');
    }

    return response.json();
  }

  /**
   * Submit feedback on a query
   */
  async submitFeedback(feedback: QueryFeedback): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/query/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedback),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit feedback');
    }
  }

  /**
   * Get query history for a session
   */
  async getHistory(sessionId: string, limit: number = 10): Promise<any[]> {
    const response = await fetch(
      `${this.baseUrl}/api/query/history/${sessionId}?limit=${limit}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get history');
    }

    return response.json();
  }

  /**
   * Clear query history for a session
   */
  async clearHistory(sessionId: string): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/query/history/${sessionId}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to clear history');
    }
  }

  /**
   * Get query statistics
   */
  async getStats(repositoryId?: string): Promise<QueryStats> {
    const url = repositoryId
      ? `${this.baseUrl}/api/query/stats?repository_id=${repositoryId}`
      : `${this.baseUrl}/api/query/stats`;

    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get stats');
    }

    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

export const apiService = new ApiService();

// Made with Bob