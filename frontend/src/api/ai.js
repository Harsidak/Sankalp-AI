/**
 * AI inference API functions.
 */

import client from './client';
import { API_BASE_URL, ENDPOINTS } from '../utils/constants';
import { getAccessToken } from '../utils/storage';

export const aiApi = {
  inference: (data) =>
    client.post(ENDPOINTS.AI.INFERENCE, data),

  getModels: () =>
    client.get(ENDPOINTS.AI.MODELS),

  generateEmbeddings: (data) =>
    client.post(ENDPOINTS.AI.EMBEDDINGS, data),

  /**
   * Stream AI response via Server-Sent Events.
   * Returns an EventSource-like interface.
   *
   * @param {Object} data - Inference request data
   * @param {Function} onToken - Callback for each token
   * @param {Function} onDone - Callback when streaming completes
   * @param {Function} onError - Callback on error
   * @returns {AbortController} - Call .abort() to cancel the stream
   */
  stream: (data, { onToken, onDone, onError }) => {
    const controller = new AbortController();

    fetch(`${API_BASE_URL}${ENDPOINTS.AI.STREAM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.slice(6));
                if (parsed.done) {
                  onDone?.();
                } else if (parsed.content) {
                  onToken?.(parsed.content);
                }
              } catch {
                // Skip malformed SSE lines
              }
            }
          }
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          onError?.(error);
        }
      });

    return controller;
  },
};
