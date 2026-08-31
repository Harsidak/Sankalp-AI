/**
 * API client constants and route paths.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// Route paths
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  DASHBOARD: '/dashboard',
  CHAT: '/chat',
};

// API endpoints
export const ENDPOINTS = {
  AUTH: {
    REGISTER: `${API_PREFIX}/auth/register`,
    LOGIN: `${API_PREFIX}/auth/login`,
    REFRESH: `${API_PREFIX}/auth/refresh`,
    GOOGLE: `${API_PREFIX}/auth/google`,
    ME: `${API_PREFIX}/auth/me`,
    LOGOUT: `${API_PREFIX}/auth/logout`,
  },
  USERS: {
    PROFILE: `${API_PREFIX}/users/me`,
    PASSWORD: `${API_PREFIX}/users/me/password`,
  },
  AI: {
    INFERENCE: `${API_PREFIX}/ai/inference`,
    STREAM: `${API_PREFIX}/ai/stream`,
    MODELS: `${API_PREFIX}/ai/models`,
    EMBEDDINGS: `${API_PREFIX}/ai/embeddings`,
  },
  RAG: {
    DOCUMENTS: `${API_PREFIX}/rag/documents`,
    QUERY: `${API_PREFIX}/rag/query`,
    QUERY_STREAM: `${API_PREFIX}/rag/query/stream`,
  },
  HEALTH: `${API_PREFIX}/health`,
};
