import { API_BASE_URL, ANOMALIES_PAGE_SIZE } from "../config";
import type {
  IAnomaliesPage,
  IFleetState,
  IHealth,
  IVehiclesResponse,
  IZonesResponse,
} from "./types";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchHealth(): Promise<IHealth> {
  return getJson<IHealth>("/health");
}

export function fetchFleetState(): Promise<IFleetState> {
  return getJson<IFleetState>("/fleet/state");
}

export function fetchVehicles(): Promise<IVehiclesResponse> {
  return getJson<IVehiclesResponse>("/vehicles");
}

export function fetchZoneCounts(): Promise<IZonesResponse> {
  return getJson<IZonesResponse>("/zones/counts");
}

export function fetchAnomalies(cursor: string | null): Promise<IAnomaliesPage> {
  const params = new URLSearchParams({ limit: String(ANOMALIES_PAGE_SIZE) });
  if (cursor !== null) {
    params.set("cursor", cursor);
  }
  return getJson<IAnomaliesPage>(`/anomalies?${params.toString()}`);
}
