/**
 * Axios API client with automatic token management.
 *
 * - Attaches Authorization header on every request
 * - On 401, attempts silent token refresh and retries the original request
 * - If refresh fails, redirects to login
 */

import axios from 'axios';
import { API_BASE_URL, ENDPOINTS } from '../utils/constants';
import { getAccessToken, getRefreshToken, setTokens, clearAll } from '../utils/storage';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// --- Request Interceptor ---
client.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- Response Interceptor (auto-refresh on 401) ---
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  failedQueue = [];
};

/**
 * Exchange the refresh token for a new pair, or join the exchange already in
 * flight.
 *
 * This is exported because the SSE stream in `api/ai.js` uses `fetch`, not
 * axios, so it never passes through the interceptor below and has to ask for
 * a refresh itself. It MUST share this single-flight lock rather than call
 * the endpoint directly: refresh tokens rotate and the old one is revoked
 * server-side, so two concurrent refreshes mean the loser presents a revoked
 * token and the user is logged out mid-demo.
 *
 * @returns {Promise<string>} the new access token
 */
export async function refreshAccessToken() {
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }

  isRefreshing = true;
  try {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token');
    }

    // Plain `axios`, not `client` — going through the instance would re-enter
    // this interceptor on failure and recurse.
    const response = await axios.post(
      `${API_BASE_URL}${ENDPOINTS.AUTH.REFRESH}`,
      { refresh_token: refreshToken }
    );

    const { access_token, refresh_token: newRefreshToken } = response.data.data;
    setTokens(access_token, newRefreshToken);
    processQueue(null, access_token);
    return access_token;
  } catch (refreshError) {
    processQueue(refreshError, null);
    clearAll();
    window.location.href = '/login';
    throw refreshError;
  } finally {
    isRefreshing = false;
  }
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Don't retry refresh token requests or already-retried requests
    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url === ENDPOINTS.AUTH.REFRESH ||
      originalRequest.url === ENDPOINTS.AUTH.LOGIN
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const token = await refreshAccessToken();
      originalRequest.headers.Authorization = `Bearer ${token}`;
      return client(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  }
);

export default client;
