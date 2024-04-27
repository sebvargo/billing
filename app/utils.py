from datetime import datetime, timezone

def utc_time_now() -> datetime:
    return datetime.now(timezone.utc)


def time_to_utc(dt):
    return dt.astimezone(timezone.utc)
