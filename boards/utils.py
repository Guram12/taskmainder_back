from datetime import datetime
import pytz
import requests

def convert_to_utc(local_time: str, user_timezone: str) -> datetime:
    """
    Converts a local time string to a UTC datetime object.

    Args:
        local_time (str): The local time in ISO 8601 format or "YYYY-MM-DD HH:MM:SS".
        user_timezone (str): The user's timezone (e.g., "Asia/Kolkata").

    Returns:
        datetime: The corresponding UTC datetime object.
    """
    try:
        # Try parsing ISO 8601 format first
        local_time_obj = datetime.fromisoformat(local_time.replace("Z", "+00:00"))
    except ValueError:
        # Fallback to parsing "YYYY-MM-DD HH:MM:SS" format
        local_time_obj = datetime.strptime(local_time, "%Y-%m-%d %H:%M:%S")
    
    # Check if the datetime object is naive (no timezone info)
    if local_time_obj.tzinfo is None:
        # Localize the naive datetime object to the user's timezone
        user_tz = pytz.timezone(user_timezone)
        localized_time = user_tz.localize(local_time_obj)
    else:
        # If already timezone-aware, assume it's in the user's timezone
        localized_time = local_time_obj

    # Convert the localized time to UTC
    utc_time = localized_time.astimezone(pytz.UTC)
    return utc_time