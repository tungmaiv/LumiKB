import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useResponsiveLayout } from '../use-responsive-layout';

// Mock matchMedia
const createMatchMedia = (matches: Record<string, boolean>) => {
  return (query: string): MediaQueryList => ({
    matches: matches[query] ?? false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(() => true),
  });
};

describe('useResponsiveLayout', () => {
  const originalMatchMedia = window.matchMedia;

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it('returns isDesktop true for viewport >= 1280px', () => {
    window.matchMedia = createMatchMedia({
      '(min-width: 1280px)': true,
      '(min-width: 1024px) and (max-width: 1279px)': false,
      '(min-width: 768px) and (max-width: 1023px)': false,
      '(max-width: 767px)': false,
    });

    const { result } = renderHook(() => useResponsiveLayout());

    expect(result.current.isDesktop).toBe(true);
    expect(result.current.isLaptop).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isMobile).toBe(false);
  });

  it('returns isLaptop true for viewport 1024-1279px', () => {
    window.matchMedia = createMatchMedia({
      '(min-width: 1280px)': false,
      '(min-width: 1024px) and (max-width: 1279px)': true,
      '(min-width: 768px) and (max-width: 1023px)': false,
      '(max-width: 767px)': false,
    });

    const { result } = renderHook(() => useResponsiveLayout());

    expect(result.current.isDesktop).toBe(false);
    expect(result.current.isLaptop).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isMobile).toBe(false);
  });

  it('returns isTablet true for viewport 768-1023px', () => {
    window.matchMedia = createMatchMedia({
      '(min-width: 1280px)': false,
      '(min-width: 1024px) and (max-width: 1279px)': false,
      '(min-width: 768px) and (max-width: 1023px)': true,
      '(max-width: 767px)': false,
    });

    const { result } = renderHook(() => useResponsiveLayout());

    expect(result.current.isDesktop).toBe(false);
    expect(result.current.isLaptop).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isMobile).toBe(false);
  });

  it('returns isMobile true for viewport < 768px', () => {
    window.matchMedia = createMatchMedia({
      '(min-width: 1280px)': false,
      '(min-width: 1024px) and (max-width: 1279px)': false,
      '(min-width: 768px) and (max-width: 1023px)': false,
      '(max-width: 767px)': true,
    });

    const { result } = renderHook(() => useResponsiveLayout());

    expect(result.current.isDesktop).toBe(false);
    expect(result.current.isLaptop).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isMobile).toBe(true);
  });
});
