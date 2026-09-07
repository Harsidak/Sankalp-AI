/**
 * AI inference API functions.
 */

import client, { refreshAccessToken } from './client';
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
   * Stream an AI response over Server-Sent Events.
   *
   * Uses `fetch` rather than the axios client because axios buffers the whole
   * response body; and rather than `EventSource` because that cannot issue a
   * POST or set an Authorization header.
   *
   * @param {Object} data - Inference request body
   * @param {Object} handlers - { onToken, onDone, onError }
   * @returns {AbortController} - Call .abort() to cancel the stream
   */
  stream: (data, { onToken, onDone, onError }) => {
    const controller = new AbortController();

    const send = (token) =>
      fetch(`${API_BASE_URL}${ENDPOINTS.AI.STREAM}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
        signal: controller.signal,
      });

    (async () => {
      let sawDone = false;
      try {
        let response = await send(getAccessToken());

        // The axios response interceptor cannot help here, so the one-shot
        // refresh-and-retry is done by hand. Without it the chat is the only
        // page in the app that breaks once the 15-minute access token expires.
        if (response.status === 401) {
          response = await send(await refreshAccessToken());
        }
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        // SSE frames are delimited by newlines, but a network chunk can end
        // mid-line. Anything after the last newline is held back and prefixed
        // onto the next chunk; parsing it immediately would drop the token
        // (JSON.parse throws) *and* orphan its remainder, which shows up as
        // words randomly missing from the reply.
        let buffer = '';

        const handleLine = (line) => {
          if (!line.startsWith('data:')) return;
          let parsed;
          try {
            parsed = JSON.parse(line.slice(5));
          } catch {
            return; // not a frame we emit; ignore
          }
          if (parsed.error) {
            throw new Error(parsed.error);
          }
          if (parsed.done) {
            sawDone = true;
            onDone?.();
          } else if (parsed.content) {
            onToken?.(parsed.content);
          }
        };

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? ''; // incomplete tail, keep for next read
          for (const line of lines) handleLine(line);
        }

        // Flush whatever the final chunk left behind.
        buffer += decoder.decode();
        if (buffer) handleLine(buffer);

        // A stream that ends without the terminating frame — the server died,
        // the provider timed out — must still clear the UI's streaming state,
        // or the typing indicator spins forever.
        if (!sawDone) {
          throw new Error('Stream ended before the model finished');
        }
      } catch (error) {
        if (error.name !== 'AbortError' && !sawDone) {
          onError?.(error);
        }
      }
    })();

    return controller;
  },
};
