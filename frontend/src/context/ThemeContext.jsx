/**
 * Theme Context Provider.
 *
 * Manages dark/light mode toggle.
 * Persists preference in localStorage.
 * Applies 'dark' class to document root for CSS targeting.
 */

import { createContext, useCallback, useEffect, useMemo, useState } from 'react';

const THEME_KEY = 'sankalp_theme';

export const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored !== null) return stored === 'dark';
    // Default to system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      localStorage.setItem(THEME_KEY, 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem(THEME_KEY, 'light');
    }
  }, [isDark]);

  const toggleTheme = useCallback(() => {
    setIsDark((prev) => !prev);
  }, []);

  const value = useMemo(
    () => ({ isDark, toggleTheme }),
    [isDark, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
