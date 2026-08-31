/**
 * RAG (Retrieval-Augmented Generation) API functions.
 */

import client from './client';
import { API_BASE_URL, ENDPOINTS } from '../utils/constants';
import { getAccessToken } from '../utils/storage';

export const ragApi = {
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post(ENDPOINTS.RAG.DOCUMENTS, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  listDocuments: () =>
    client.get(ENDPOINTS.RAG.DOCUMENTS),

  deleteDocument: (documentId) =>
    client.delete(`${ENDPOINTS.RAG.DOCUMENTS}/${documentId}`),

  query: (data) =>
    client.post(ENDPOINTS.RAG.QUERY, data),

  /**
   * Stream RAG query response via SSE.
   */
  queryStream: (data, { onToken, onDone, onError }) => {
    const controller = new AbortController();

    fetch(`${API_BASE_URL}${ENDPOINTS.RAG.QUERY_STREAM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

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
                // Skip malformed lines
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
