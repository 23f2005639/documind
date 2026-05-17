/**
 * Source Panel Component
 * Displays source citations in a side panel
 */

import React from 'react';
import { Source } from '../types/query';
import { X, FileCode, FileText, ExternalLink } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface SourcePanelProps {
  sources: Source[];
  onClose: () => void;
}

const SourcePanel: React.FC<SourcePanelProps> = ({ sources, onClose }) => {
  const getLanguageFromPath = (path?: string): string => {
    if (!path) return 'text';
    const ext = path.split('.').pop()?.toLowerCase();
    const langMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'jsx': 'javascript',
      'java': 'java',
      'go': 'go',
      'rs': 'rust',
      'cpp': 'cpp',
      'c': 'c',
      'rb': 'ruby',
      'php': 'php',
      'sql': 'sql',
      'sh': 'bash',
      'yaml': 'yaml',
      'yml': 'yaml',
      'json': 'json',
      'md': 'markdown'
    };
    return langMap[ext || ''] || 'text';
  };

  return (
    <div className="w-96 border-l border-gray-200 bg-white flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Sources ({sources.length})
        </h2>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Sources list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {sources.map((source, idx) => (
          <div
            key={idx}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            {/* Source header */}
            <div className="bg-gray-50 px-3 py-2 border-b border-gray-200">
              <div className="flex items-center gap-2">
                {source.type === 'code' ? (
                  <FileCode size={16} className="text-blue-600" />
                ) : (
                  <FileText size={16} className="text-green-600" />
                )}
                <span className="text-xs font-medium text-gray-700">
                  {source.type === 'code' ? 'Code' : 'Documentation'}
                </span>
                <span className="ml-auto text-xs text-gray-500">
                  {(source.relevance_score * 100).toFixed(0)}% relevant
                </span>
              </div>

              {/* File path or doc title */}
              {source.file_path && (
                <div className="mt-1 text-xs text-gray-600 font-mono truncate">
                  {source.file_path}
                  {source.line_start && (
                    <span className="text-gray-400">
                      :{source.line_start}
                      {source.line_end && source.line_end !== source.line_start
                        ? `-${source.line_end}`
                        : ''}
                    </span>
                  )}
                </div>
              )}

              {source.documentation_title && (
                <div className="mt-1 text-xs text-gray-600 truncate">
                  {source.documentation_title}
                </div>
              )}
            </div>

            {/* Source content */}
            <div className="p-3">
              {source.type === 'code' && source.file_path ? (
                <div className="text-xs">
                  <SyntaxHighlighter
                    language={getLanguageFromPath(source.file_path)}
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      padding: '0.5rem',
                      fontSize: '0.75rem',
                      maxHeight: '200px',
                      overflow: 'auto'
                    }}
                  >
                    {source.content}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <div className="text-xs text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {source.content}
                </div>
              )}
            </div>

            {/* View full link */}
            {source.documentation_id && (
              <div className="px-3 py-2 bg-gray-50 border-t border-gray-200">
                <a
                  href={`/documentation/${source.documentation_id}`}
                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink size={12} />
                  View full documentation
                </a>
              </div>
            )}
          </div>
        ))}

        {sources.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <FileText size={48} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No sources available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourcePanel;

// Made with Bob