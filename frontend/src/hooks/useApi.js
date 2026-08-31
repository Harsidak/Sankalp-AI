/**
 * Generic API call hook with loading, error, and data state management.
 */

import { useCallback, useState } from 'react';

export function useApi(apiFunction) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const execute = useCallback(
    async (...args) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiFunction(...args);
        const result = response.data;
        setData(result);
        return result;
      } catch (err) {
        const errorMessage =
          err.response?.data?.error?.message ||
          err.message ||
          'An unexpected error occurred';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return { data, error, isLoading, execute, reset };
}
