/**
 * Hook for fetching and updating system configuration settings.
 */

import { useState } from "react";
import { ConfigSetting, ConfigUpdateResponse } from "@/types/config";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseSystemConfigReturn {
  configs: Record<string, ConfigSetting> | undefined;
  isLoading: boolean;
  error: Error | null;
  updateConfig: (key: string, value: number | boolean | string) => Promise<void>;
  isUpdating: boolean;
  updateError: Error | null;
  refetch: () => Promise<void>;
}

export function useSystemConfig(): UseSystemConfigReturn {
  const [configs, setConfigs] = useState<Record<string, ConfigSetting> | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<Error | null>(null);

  const fetchConfigs = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/config`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch config: ${response.status}`);
      }

      const data = await response.json();
      setConfigs(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setIsLoading(false);
    }
  };

  const updateConfig = async (key: string, value: number | boolean | string) => {
    setIsUpdating(true);
    setUpdateError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/config/${key}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ value }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to update config: ${response.status}`);
      }

      const data: ConfigUpdateResponse = await response.json();

      // Update local configs
      setConfigs((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          [key]: data.setting,
        };
      });

      // Refetch to ensure consistency
      await fetchConfigs();
    } catch (err) {
      setUpdateError(err instanceof Error ? err : new Error("Unknown error"));
      throw err;
    } finally {
      setIsUpdating(false);
    }
  };

  // Auto-fetch on mount
  if (configs === undefined && !isLoading && !error) {
    fetchConfigs();
  }

  return {
    configs,
    isLoading,
    error,
    updateConfig,
    isUpdating,
    updateError,
    refetch: fetchConfigs,
  };
}
