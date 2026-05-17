/**
 * Message List Component
 * Displays conversation messages with sources and feedback
 */

import React from 'react';
import { Message, Source } from '../types/query';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ThumbsUp, ThumbsDown, FileCode, FileText, ExternalLink } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
  currentAnswer: string;
  currentSources: Source[];
  isStreaming: boolean;
  onFeedback: (messageId: string, feedback: -1 | 0 | 1) => void;
  onRelatedQuestion: (question: string) => void;
  onViewSources: (sources: Source[]) => void;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  currentAnswer,
  currentSources,
  isStreaming,
  onFeedback,
  onRelatedQuestion,
  onViewSources
}) => {
  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
          {/* Message bubble */}
          <div
            className={`rounded-lg px-4 py-3 ${
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-200 text-gray-900'
            }`}
          >
            {isUser ? (
              <p className="text-sm">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    code({ className, children, ...props }) {
                      const match = (className || '').match(/language-(\w+)/);
                      return match ? (
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Assistant message metadata */}
          {!isUser && (
            <div className="mt-2 space-y-2">
              {/* Confidence score */}
              {message.confidence_score !== undefined && (
                <div className="flex items-center text-xs text-gray-500">
                  <span>Confidence: {(message.confidence_score * 100).toFixed(0)}%</span>
                </div>
              )}

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onViewSources(message.sources!)}
                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <ExternalLink size={12} />
                    View {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                  </button>
                </div>
              )}

              {/* Related questions */}
              {message.related_questions && message.related_questions.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-2">Related questions:</p>
                  <div className="space-y-1">
                    {message.related_questions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => onRelatedQuestion(q)}
                        className="block text-xs text-blue-600 hover:text-blue-800 hover:underline text-left"
                      >
                        • {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback buttons */}
              <div className="flex items-center gap-2 mt-2">
                <button
                  onClick={() => onFeedback(message.id, 1)}
                  className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                  title="Helpful"
                >
                  <ThumbsUp size={14} />
                </button>
                <button
                  onClick={() => onFeedback(message.id, -1)}
                  className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  title="Not helpful"
                >
                  <ThumbsDown size={14} />
                </button>
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="mt-1 text-xs text-gray-400">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Existing messages */}
      {messages.map(renderMessage)}

      {/* Current streaming answer */}
      {isStreaming && currentAnswer && (
        <div className="flex justify-start mb-4">
          <div className="max-w-3xl mr-12">
            <div className="rounded-lg px-4 py-3 bg-white border border-gray-200 text-gray-900">
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{currentAnswer}</ReactMarkdown>
              </div>
              {/* Typing indicator */}
              <div className="flex items-center gap-1 mt-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>

            {/* Current sources */}
            {currentSources.length > 0 && (
              <div className="mt-2 text-xs text-gray-500">
                Found {currentSources.length} relevant source{currentSources.length > 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading indicator when no answer yet */}
      {isStreaming && !currentAnswer && (
        <div className="flex justify-start mb-4">
          <div className="max-w-3xl mr-12">
            <div className="rounded-lg px-4 py-3 bg-white border border-gray-200">
              <div className="flex items-center gap-2 text-gray-500">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {messages.length === 0 && !isStreaming && (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
            <FileCode className="text-blue-600" size={32} />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ask me anything about your codebase
          </h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            I can help you understand code, find documentation, and answer technical questions.
          </p>
        </div>
      )}
    </div>
  );
};

export default MessageList;

// Made with Bob