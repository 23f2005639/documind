/**
 * Main Query Interface Component
 * Handles user questions with streaming responses
 */

import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import { Message, Source, StreamEvent } from '../types/query';
import MessageList from './MessageList';
import QueryInput from './QueryInput';
import SourcePanel from './SourcePanel';

interface QueryInterfaceProps {
  repositoryId?: string;
  sessionId?: string;
}

const QueryInterface: React.FC<QueryInterfaceProps> = ({
  repositoryId,
  sessionId: initialSessionId
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState<string>('');
  const [currentSources, setCurrentSources] = useState<Source[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>(
    initialSessionId || `session-${Date.now()}`
  );
  const [selectedSources, setSelectedSources] = useState<Source[]>([]);
  const [showSources, setShowSources] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAnswer]);

  // Handle streaming query
  const handleStreamingQuery = async (question: string) => {
    setError(null);
    setIsStreaming(true);
    setCurrentAnswer('');
    setCurrentSources([]);

    // Add user message
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const query = {
        question,
        repository_id: repositoryId,
        session_id: sessionId,
        max_results: 10,
        include_code: true,
        include_docs: true
      };

      let fullAnswer = '';
      let sources: Source[] = [];
      let relatedQuestions: string[] = [];
      let confidence = 0;

      for await (const event of apiService.streamQuestion(query)) {
        switch (event.type) {
          case 'sources':
            sources = event.data || [];
            setCurrentSources(sources);
            break;

          case 'chunk':
            if (event.content) {
              fullAnswer += event.content;
              setCurrentAnswer(fullAnswer);
            }
            break;

          case 'answer':
            fullAnswer = event.content || fullAnswer;
            setCurrentAnswer(fullAnswer);
            break;

          case 'done':
            // Add assistant message
            const assistantMessage: Message = {
              id: `msg-${Date.now()}`,
              role: 'assistant',
              content: fullAnswer,
              sources,
              confidence_score: confidence,
              related_questions: relatedQuestions,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, assistantMessage]);
            setCurrentAnswer('');
            setCurrentSources([]);
            break;

          case 'error':
            setError(event.message || 'An error occurred');
            break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
      console.error('Streaming error:', err);
    } finally {
      setIsStreaming(false);
    }
  };

  // Handle non-streaming query (fallback)
  const handleQuery = async (question: string) => {
    setError(null);
    setIsStreaming(true);

    // Add user message
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await apiService.askQuestion({
        question,
        repository_id: repositoryId,
        session_id: sessionId,
        max_results: 10,
        include_code: true,
        include_docs: true
      });

      // Add assistant message
      const assistantMessage: Message = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence_score: response.confidence_score,
        related_questions: response.related_questions,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
      console.error('Query error:', err);
    } finally {
      setIsStreaming(false);
    }
  };

  // Handle feedback
  const handleFeedback = async (messageId: string, feedback: -1 | 0 | 1) => {
    try {
      await apiService.submitFeedback({
        query_id: messageId,
        feedback
      });
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  // Handle related question click
  const handleRelatedQuestion = (question: string) => {
    handleStreamingQuery(question);
  };

  // View sources
  const handleViewSources = (sources: Source[]) => {
    setSelectedSources(sources);
    setShowSources(true);
  };

  // Clear conversation
  const handleClear = async () => {
    try {
      await apiService.clearHistory(sessionId);
      setMessages([]);
      setCurrentAnswer('');
      setCurrentSources([]);
      setError(null);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">DocuMind</h1>
              <p className="text-sm text-gray-500">Ask questions about your codebase</p>
            </div>
            <button
              onClick={handleClear}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Clear Chat
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <MessageList
            messages={messages}
            currentAnswer={currentAnswer}
            currentSources={currentSources}
            isStreaming={isStreaming}
            onFeedback={handleFeedback}
            onRelatedQuestion={handleRelatedQuestion}
            onViewSources={handleViewSources}
          />
          <div ref={messagesEndRef} />
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-6 mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Input */}
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <QueryInput
            onSubmit={handleStreamingQuery}
            disabled={isStreaming}
            placeholder="Ask a question about your codebase..."
          />
        </div>
      </div>

      {/* Source panel */}
      {showSources && (
        <SourcePanel
          sources={selectedSources}
          onClose={() => setShowSources(false)}
        />
      )}
    </div>
  );
};

export default QueryInterface;

// Made with Bob