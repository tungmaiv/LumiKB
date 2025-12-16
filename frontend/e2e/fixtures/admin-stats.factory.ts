/**
 * Admin Statistics Factory
 * Story 5-1 Automation: Reusable mock data for admin dashboard tests
 *
 * Provides factory functions to generate consistent mock admin statistics
 * data for E2E and component tests.
 */

export interface AdminStatsData {
  users: {
    total: number;
    active: number;
    inactive: number;
  };
  knowledge_bases: {
    total: number;
    by_status: Record<string, number>;
  };
  documents: {
    total: number;
    by_status: Record<string, number>;
  };
  storage: {
    total_bytes: number;
    avg_doc_size_bytes: number;
  };
  activity: {
    searches: {
      last_24h: number;
      last_7d: number;
      last_30d: number;
    };
    generations: {
      last_24h: number;
      last_7d: number;
      last_30d: number;
    };
  };
  trends: {
    searches: number[];
    generations: number[];
  };
}

/**
 * Create default admin stats with realistic data
 */
export function createAdminStats(overrides?: Partial<AdminStatsData>): AdminStatsData {
  const defaults: AdminStatsData = {
    users: {
      total: 100,
      active: 80,
      inactive: 20,
    },
    knowledge_bases: {
      total: 50,
      by_status: {
        active: 45,
        archived: 5,
      },
    },
    documents: {
      total: 1000,
      by_status: {
        READY: 900,
        PENDING: 50,
        PROCESSING: 25,
        FAILED: 25,
      },
    },
    storage: {
      total_bytes: 1073741824, // 1GB
      avg_doc_size_bytes: 1048576, // 1MB
    },
    activity: {
      searches: {
        last_24h: 100,
        last_7d: 700,
        last_30d: 3000,
      },
      generations: {
        last_24h: 50,
        last_7d: 350,
        last_30d: 1500,
      },
    },
    trends: {
      searches: Array.from({ length: 30 }, (_, i) => 90 + i),
      generations: Array.from({ length: 30 }, (_, i) => 45 + i),
    },
  };

  return deepMerge(defaults, overrides || {});
}

/**
 * Create empty admin stats (for empty database scenarios)
 */
export function createEmptyAdminStats(): AdminStatsData {
  return {
    users: {
      total: 0,
      active: 0,
      inactive: 0,
    },
    knowledge_bases: {
      total: 0,
      by_status: {},
    },
    documents: {
      total: 0,
      by_status: {},
    },
    storage: {
      total_bytes: 0,
      avg_doc_size_bytes: 0,
    },
    activity: {
      searches: {
        last_24h: 0,
        last_7d: 0,
        last_30d: 0,
      },
      generations: {
        last_24h: 0,
        last_7d: 0,
        last_30d: 0,
      },
    },
    trends: {
      searches: Array(30).fill(0),
      generations: Array(30).fill(0),
    },
  };
}

/**
 * Create admin stats with high activity (for performance testing)
 */
export function createHighActivityAdminStats(): AdminStatsData {
  return createAdminStats({
    users: {
      total: 1000,
      active: 850,
      inactive: 150,
    },
    knowledge_bases: {
      total: 500,
      by_status: {
        active: 475,
        archived: 25,
      },
    },
    documents: {
      total: 100000,
      by_status: {
        READY: 95000,
        PENDING: 2500,
        PROCESSING: 1500,
        FAILED: 1000,
      },
    },
    storage: {
      total_bytes: 107374182400, // 100GB
      avg_doc_size_bytes: 1073741, // ~1MB
    },
    activity: {
      searches: {
        last_24h: 5000,
        last_7d: 35000,
        last_30d: 150000,
      },
      generations: {
        last_24h: 2500,
        last_7d: 17500,
        last_30d: 75000,
      },
    },
    trends: {
      searches: Array.from({ length: 30 }, (_, i) => 4500 + i * 20),
      generations: Array.from({ length: 30 }, (_, i) => 2250 + i * 10),
    },
  });
}

/**
 * Create admin stats with declining trend (for testing negative growth)
 */
export function createDecliningTrendAdminStats(): AdminStatsData {
  return createAdminStats({
    trends: {
      searches: Array.from({ length: 30 }, (_, i) => 150 - i * 2),
      generations: Array.from({ length: 30 }, (_, i) => 75 - i),
    },
  });
}

/**
 * Create admin stats with flat trend (no growth)
 */
export function createFlatTrendAdminStats(): AdminStatsData {
  return createAdminStats({
    trends: {
      searches: Array(30).fill(100),
      generations: Array(30).fill(50),
    },
  });
}

/**
 * Deep merge helper for partial overrides
 */
function deepMerge(
  target: AdminStatsData,
  source: Partial<AdminStatsData>
): AdminStatsData {
  const result = { ...target };

  for (const key in source) {
    const sourceValue = source[key as keyof AdminStatsData];
    const targetValue = result[key as keyof AdminStatsData];

    if (
      sourceValue &&
      typeof sourceValue === 'object' &&
      !Array.isArray(sourceValue) &&
      targetValue &&
      typeof targetValue === 'object' &&
      !Array.isArray(targetValue)
    ) {
      (result[key as keyof AdminStatsData] as Record<string, unknown>) = {
        ...targetValue,
        ...sourceValue,
      };
    } else if (sourceValue !== undefined) {
      (result[key as keyof AdminStatsData] as typeof sourceValue) = sourceValue;
    }
  }

  return result;
}
