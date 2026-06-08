const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export const ANOMALIES_PAGE_SIZE = 15;

export const BATTERY_CRITICAL_PCT = 15;
export const BATTERY_WARNING_PCT = 40;

export const POLL_INTERVALS = {
  fleetState: 1000,
  vehicles: 1000,
  zoneCounts: 1000,
  anomalies: 2000,
  health: 5000,
} as const;
