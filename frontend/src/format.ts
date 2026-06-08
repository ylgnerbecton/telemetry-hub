import { BATTERY_CRITICAL_PCT, BATTERY_WARNING_PCT } from "./config";
import type { TAnomalySeverity, TVehicleStatus } from "./api/types";

export type TChipColor =
  | "default"
  | "primary"
  | "secondary"
  | "info"
  | "success"
  | "warning"
  | "error";

const STATUS_COLOR: Record<TVehicleStatus, TChipColor> = {
  idle: "default",
  moving: "primary",
  charging: "info",
  fault: "error",
};

const SEVERITY_COLOR: Record<TAnomalySeverity, TChipColor> = {
  low: "default",
  medium: "info",
  high: "warning",
  critical: "error",
};

export function statusColor(status: TVehicleStatus): TChipColor {
  return STATUS_COLOR[status];
}

export function severityColor(severity: TAnomalySeverity): TChipColor {
  return SEVERITY_COLOR[severity];
}

export function batteryColor(percent: number): "error" | "warning" | "success" {
  if (percent < BATTERY_CRITICAL_PCT) {
    return "error";
  }
  if (percent < BATTERY_WARNING_PCT) {
    return "warning";
  }
  return "success";
}

export function formatTime(value: string | null): string {
  if (value === null) {
    return "-";
  }
  return new Date(value).toLocaleTimeString();
}
