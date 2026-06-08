from enum import Enum


class VehicleStatus(str, Enum):
    IDLE = "idle"
    MOVING = "moving"
    CHARGING = "charging"
    FAULT = "fault"


class MissionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class MaintenanceStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    LOW_BATTERY = "low_battery"
    FAULT_STATUS = "fault_status"
    ERROR_CODE = "error_code"
    OVERSPEED = "overspeed"
    STALE_TIMESTAMP = "stale_timestamp"


SEVERITY_BY_TYPE: dict[AnomalyType, AnomalySeverity] = {
    AnomalyType.FAULT_STATUS: AnomalySeverity.CRITICAL,
    AnomalyType.LOW_BATTERY: AnomalySeverity.HIGH,
    AnomalyType.ERROR_CODE: AnomalySeverity.MEDIUM,
    AnomalyType.OVERSPEED: AnomalySeverity.MEDIUM,
    AnomalyType.STALE_TIMESTAMP: AnomalySeverity.LOW,
}
