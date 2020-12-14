from datetime import datetime, timedelta


def parse_time(time):
    """Convert human time to timestamp"""
    if isinstance(time, datetime):
        time = datetime.timestamp(time)
    elif isinstance(time, timedelta):
        time = time.total_seconds()
    else:
        time = time
    return time
