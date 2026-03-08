"""
時區轉換工具模組
================

將 UTC 時間戳轉換為配置的本地時區，用於 API 回傳顯示。
存儲層維持 UTC 不變，僅在輸出層轉換。
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_display_tz: ZoneInfo = ZoneInfo("UTC")


def configure_timezone(tz_name: str) -> None:
    """設定顯示時區，啟動時調用一次。"""
    global _display_tz
    _display_tz = ZoneInfo(tz_name)


def format_timestamp(dt) -> str:
    """將 UTC 時間戳轉換為配置的本地時區 ISO 字串。"""
    if not dt:
        return ""
    if isinstance(dt, str):
        if not dt:
            return ""
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(_display_tz).isoformat()
    return str(dt)
