/**
 * Authentication Context Provider.
 *
 * Manages global auth state: user object, tokens, loading state.
 * On mount, checks localStorage for existing tokens and validates with /auth/me.
 * Provides login, signup, googleLogin, logout actions to all child components.
 */

import { createContext, useCallback, useEffect, useMemo, useReducer } from 'react';
import { authApi } from '../api/auth';
import {
  clearAll,
  getAccessToken,
  getRefreshToken,
  setStoredUser,
  setTokens,
} from '../utils/storage';

// Initial state
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
};

// Reducer actions
const AUTH_ACTIONS = {
  SET_USER: 'SET_USER',
  LOGOUT: 'LOGOUT',
  SET_LOADING: 'SET_LOADING',
};

function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.SET_USER:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      };
    case AUTH_ACTIONS.SET_LOADING:
      return { ...state, isLoading: action.payload };
    default:
      return state;
  }
}

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // --- Hydrate auth state from localStorage on mount ---
  useEffect(() => {
    const initAuth = async () => {
      const token = getAccessToken();
      if (!token) {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
        return;
      }

      try {
        const response = await authApi.getMe();
        const user = response.data.data;
        setStoredUser(user);
        dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
      } catch {
        clearAll();
        dispatch({ type: AUTH_ACTIONS.LOGOUT });
      }
    };

    initAuth();
  }, []);

  // --- Auth actions ---

  const login = useCallback(async (email, password) => {
    const response = await authApi.login({ email, password });
    const { access_token, refresh_token } = response.data.data;
    setTokens(access_token, refresh_token);

    const meResponse = await authApi.getMe();
    const user = meResponse.data.data;
    setStoredUser(user);
    dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
    return user;
  }, []);

  const signup = useCallback(async (email, password, fullName) => {
    const response = await authApi.register({ email, password, full_name: fullName });
    const { access_token, refresh_token } = response.data.data;
    setTokens(access_token, refresh_token);

    const meResponse = await authApi.getMe();
    const user = meResponse.data.data;
    setStoredUser(user);
    dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
    return user;
  }, []);

  const loginWithGoogle = useCallback(async (code, idToken) => {
    const response = await authApi.googleAuth({ code, id_token: idToken });
    const { access_token, refresh_token } = response.data.data;
    setTokens(access_token, refresh_token);

    const meResponse = await authApi.getMe();
    const user = meResponse.data.data;
    setStoredUser(user);
    dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
    return user;
  }, []);

  /**
   * Re-reads the profile from the server. Settings calls this after saving,
   * so the name in the navbar changes with the one in the form instead of
   * waiting for a reload.
   */
  const refreshUser = useCallback(async () => {
    const response = await authApi.getMe();
    const user = response.data.data;
    setStoredUser(user);
    dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
    return user;
  }, []);

  const logout = useCallback(async () => {
    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Logout even if server call fails
    } finally {
      clearAll();
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  }, []);

  const value = useMemo(
    () => ({
      ...state,
      login,
      signup,
      loginWithGoogle,
      logout,
      refreshUser,
    }),
    [state, login, signup, loginWithGoogle, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
