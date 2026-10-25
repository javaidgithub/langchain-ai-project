from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.tools import tool


@tool
def get_current_datetime(timezone: str = "UTC") -> str:
    """Get the current date and time in an IANA timezone, e.g. "UTC", "Asia/Karachi", "America/New_York"."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        return f"Unknown timezone '{timezone}'. Use an IANA name like 'Europe/London'."
    return now.strftime("%A, %d %B %Y, %H:%M:%S %Z (UTC%z)")
