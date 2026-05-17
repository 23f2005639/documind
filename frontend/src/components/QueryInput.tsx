/**
 * Query Input Component
 * Text input for asking questions
 */

import React, { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

interface QueryInputProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  disabled = false,
  placeholder = 'Ask a question...'
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSubmit(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-end gap-2">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
        style={{ minHeight: '48px', maxHeight: '200px' }}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
      >
        <Send size={18} />
        <span className="hidden sm:inline">Send</span>
      </button>
    </div>
  );
};

export default QueryInput;

// Made with Bob