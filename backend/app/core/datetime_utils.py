from datetime import datetime, timezone


def parse_date_range(date_from: str | None, date_to: str | None) -> tuple[datetime | None, datetime | None]:
    """Parse date strings to datetime. Returns (start, end) for filtering."""
    if date_from:
        try:
            start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"date_from 格式无效，请使用 ISO 格式，如 2026-04-01")
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
    else:
        start = None

    if date_to:
        try:
            end = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"date_to 格式无效，请使用 ISO 格式，如 2026-04-09")
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        # 将 end 设为当天结束
        from datetime import timedelta
        end = end.replace(hour=23, minute=59, second=59)
    else:
        end = None

    return start, end
