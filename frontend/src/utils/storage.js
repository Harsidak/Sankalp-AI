/**
 * LocalStorage helpers for token management.
 *
 * Centralizes all localStorage access so token key names
 * are defined in one place and never hardcoded in components.
 */

const KEYS = {
  ACCESS_TOKEN: 'sankalp_access_token',
  REFRESH_TOKEN: 'sankalp_refresh_token',
  USER: 'sankalp_user',
};

// --- Token Management ---

export const getAccessToken = () => localStorage.getItem(KEYS.ACCESS_TOKEN);
export const getRefreshToken = () => localStorage.getItem(KEYS.REFRESH_TOKEN);

export const setTokens = (accessToken, refreshToken) => {
  localStorage.setItem(KEYS.ACCESS_TOKEN, accessToken);
  localStorage.setItem(KEYS.REFRESH_TOKEN, refreshToken);
};

export const clearTokens = () => {
  localStorage.removeItem(KEYS.ACCESS_TOKEN);
  localStorage.removeItem(KEYS.REFRESH_TOKEN);
};

// --- User Data ---

export const getStoredUser = () => {
  const data = localStorage.getItem(KEYS.USER);
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
};

export const setStoredUser = (user) => {
  localStorage.setItem(KEYS.USER, JSON.stringify(user));
};

export const clearStoredUser = () => {
  localStorage.removeItem(KEYS.USER);
};

// --- Clear Everything ---

export const clearAll = () => {
  clearTokens();
  clearStoredUser();
};
