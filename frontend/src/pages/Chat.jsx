/**
 * AI Chat page — streaming chat interface.
 */

import { useRef, useEffect, useState } from 'react';
import { useChat } from '../hooks/useChat';
import Navbar from '../components/layout/Navbar';

export default function Chat() {
  const { messages, isStreaming, sendMessage, stopStreaming, clearMessages } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    sendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-page">
      <Navbar />

      <div className="chat-container">
        {/* Chat Header */}
        <div className="chat-header">
          <h2>AI Chat</h2>
          <div className="chat-header-actions">
            <button
              onClick={clearMessages}
              className="btn btn-outline btn-sm"
              disabled={messages.length === 0}
            >
              Clear Chat
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <div className="chat-empty-icon">🤖</div>
              <h3>Start a conversation</h3>
              <p>Ask anything — I'm powered by state-of-the-art AI models.</p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-message chat-message-${msg.role}`}
            >
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <div className="message-text">
                  {msg.content || (msg.isStreaming ? '...' : '')}
                </div>
                {msg.isStreaming && (
                  <span className="streaming-indicator">●</span>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="chat-input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            className="chat-input"
            rows={1}
            disabled={isStreaming}
          />
          {isStreaming ? (
            <button
              type="button"
              onClick={stopStreaming}
              className="btn btn-danger"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!input.trim()}
            >
              Send
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
