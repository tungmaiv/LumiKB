/**
 * useDebounce Hook
 * Returns a debounced value that only updates after the specified delay
 */

import { useEffect, useState } from 'react';

/**
 * Debounces a value, delaying updates until after the specified delay.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 500)
 * @returns Debounced value
 *
 * @example
 * const searchTerm = useDebounce(inputValue, 300);
 * // searchTerm only updates 300ms after user stops typing
 */
export function useDebounce<T>(value: T, delay = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
