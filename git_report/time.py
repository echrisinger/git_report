from datetime import datetime

from dateutil.tz import tzlocal


def local_time():
    return datetime.now(tzlocal())
