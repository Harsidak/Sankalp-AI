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
  CHECKIN: '/checkin',
  JOURNAL: '/journal',
  HABITS: '/habits',
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
    REFLECT: `${API_PREFIX}/ai/reflect`,
  },
  CHECKINS: {
    ROOT: `${API_PREFIX}/checkins`,
    TODAY: `${API_PREFIX}/checkins/today`,
    STREAK: `${API_PREFIX}/checkins/streak`,
    ONE: (id) => `${API_PREFIX}/checkins/${id}`,
  },
  JOURNAL: {
    ROOT: `${API_PREFIX}/journal`,
    ONE: (id) => `${API_PREFIX}/journal/${id}`,
  },
  HABITS: {
    ROOT: `${API_PREFIX}/habits`,
    ONE: (id) => `${API_PREFIX}/habits/${id}`,
    LOG: (id) => `${API_PREFIX}/habits/${id}/log`,
  },
  TAGS: {
    ROOT: `${API_PREFIX}/tags`,
    ONE: (id) => `${API_PREFIX}/tags/${id}`,
  },
  DASHBOARD: {
    SUMMARY: `${API_PREFIX}/dashboard/summary`,
  },
  HEALTH: `${API_PREFIX}/health`,
};
