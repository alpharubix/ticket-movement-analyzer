from datetime import datetime


def format_duration(seconds):
    """Converts seconds into H:MM format string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes:02d}m"

def parse_time(time_str):
    """Parses ISO string, handling the 'Z' for UTC."""
    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))