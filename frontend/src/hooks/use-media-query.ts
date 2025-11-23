'use client';

import { useSyncExternalStore } from 'react';

function getServerSnapshot(): boolean {
  return false;
}

export function useMediaQuery(query: string): boolean {
  const subscribe = (callback: () => void): (() => void) => {
    const mediaQuery = window.matchMedia(query);
    mediaQuery.addEventListener('change', callback);
    return () => mediaQuery.removeEventListener('change', callback);
  };

  const getSnapshot = (): boolean => {
    return window.matchMedia(query).matches;
  };

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
