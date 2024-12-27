from datetime import datetime

from viessmann_bridge.config import get_config


def to_local_time(utc: datetime) -> datetime:
    config = get_config()

    local_dt = utc.astimezone(config.timezone)
    return local_dt


def parse_time(raw: str) -> datetime:
    return to_local_time(datetime.fromisoformat(raw))
