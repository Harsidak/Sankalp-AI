/**
 * Chat hook for managing AI chat sessions with streaming support.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { aiApi } from '../api/ai';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const controllerRef = useRef(null);

  // The message list is also the request context, so `sendMessage` reads it
  // through a ref rather than closing over it -- otherwise the callback would
  // be re-created on every streamed token, defeating the memoisation it
  // exists for. The ref is synced in an effect, not during render: writing a
  // ref while rendering is a side effect and React may discard that render.
  // `sendMessage` only ever runs from a user event, long after paint, so the
  // effect has always committed by then.
  const messagesRef = useRef([]);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const sendMessage = useCallback(
    async (prompt, options = {}) => {
      // Prior turns, oldest first. Streaming placeholders and failed turns are
      // excluded: replaying an empty or errored assistant message would teach
      // the model that blank replies are acceptable. Capped to the last 20 to
      // match the server-side limit.
      const history = messagesRef.current
        .filter((m) => m.content && !m.isError && !m.isStreaming)
        .slice(-20)
        .map((m) => ({ role: m.role, content: m.content }));

      // Add user message
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: prompt,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Add placeholder for assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsStreaming(true);

      // Stream the response
      controllerRef.current = aiApi.stream(
        {
          prompt,
          history,
          system_prompt: options.systemPrompt,
          model: options.model,
          provider: options.provider,
          max_tokens: options.maxTokens || 1024,
          temperature: options.temperature || 0.7,
        },
        {
          onToken: (token) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  content: last.content + token,
                };
              }
              return updated;
            });
          },
          onDone: () => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  isStreaming: false,
                };
              }
              return updated;
            });
            setIsStreaming(false);
          },
          onError: (error) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  content: `Error: ${error.message}`,
                  isStreaming: false,
                  isError: true,
                };
              }
              return updated;
            });
            setIsStreaming(false);
          },
        }
      );
    },
    []
  );

  const stopStreaming = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setIsStreaming(false);
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last?.isStreaming) {
        updated[updated.length - 1] = { ...last, isStreaming: false };
      }
      return updated;
    });
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isStreaming,
    sendMessage,
    stopStreaming,
    clearMessages,
  };
}
