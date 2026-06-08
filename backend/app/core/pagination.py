import base64
import binascii
import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CursorPosition:
    observed_at: datetime
    anomaly_id: uuid.UUID


class InvalidCursorError(ValueError):
    pass


def encode_cursor(position: CursorPosition) -> str:
    raw = f"{position.observed_at.isoformat()}|{position.anomaly_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> CursorPosition:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        observed_raw, id_raw = raw.split("|", 1)
        return CursorPosition(
            observed_at=datetime.fromisoformat(observed_raw),
            anomaly_id=uuid.UUID(id_raw),
        )
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        raise InvalidCursorError("invalid cursor") from error
