export type TVehicleStatus = "idle" | "moving" | "charging" | "fault";

export type TAnomalyType =
  | "low_battery"
  | "fault_status"
  | "error_code"
  | "overspeed"
  | "stale_timestamp";

export type TAnomalySeverity = "low" | "medium" | "high" | "critical";

export interface IAnomalyBrief {
  type: TAnomalyType;
  severity: TAnomalySeverity;
  message: string;
  observed_at: string;
}

export interface IVehicle {
  vehicle_id: string;
  current_status: TVehicleStatus;
  battery_pct: number | null;
  speed_mps: number | null;
  lat: number | null;
  lon: number | null;
  last_seen_at: string | null;
  most_recent_anomaly: IAnomalyBrief | null;
}

export interface IVehiclesResponse {
  vehicles: IVehicle[];
}

export interface IFleetStatusCounts {
  idle: number;
  moving: number;
  charging: number;
  fault: number;
}

export interface IFleetState {
  total: number;
  by_status: IFleetStatusCounts;
  generated_at: string;
}

export interface IZoneCount {
  zone_id: string;
  entry_count: number;
  updated_at: string;
}

export interface IZonesResponse {
  zones: IZoneCount[];
}

export interface IAnomaly {
  id: string;
  vehicle_id: string;
  type: TAnomalyType;
  severity: TAnomalySeverity;
  message: string;
  observed_at: string;
  metadata: Record<string, unknown>;
}

export interface IAnomaliesPage {
  items: IAnomaly[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface IHealth {
  status: string;
}
