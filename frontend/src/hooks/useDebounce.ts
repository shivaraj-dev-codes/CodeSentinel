import { useEffect, useState } from "react";

/**
 * Debounce a value by the given delay (ms).
 * Returns the debounced value, which only updates after the delay.
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
