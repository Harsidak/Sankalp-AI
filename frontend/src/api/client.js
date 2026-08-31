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

    if (isRefreshing) {
      // Queue the request while refresh is in progress
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return client(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearAll();
      window.location.href = '/login';
      return Promise.reject(error);
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}${ENDPOINTS.AUTH.REFRESH}`,
        { refresh_token: refreshToken }
      );

      const { access_token, refresh_token: newRefreshToken } = response.data.data;
      setTokens(access_token, newRefreshToken);

      processQueue(null, access_token);

      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return client(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearAll();
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default client;
