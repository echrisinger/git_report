from abc import abstractclassmethod
from typing import NamedTuple

from dateutil import parser


class FswatchEvent(NamedTuple):
    timestamp: str
    file_name: str

    @classmethod
    def coerce(cls, timestamp, file_name):
        timestamp = parser.parse(timestamp)
        return cls(str(timestamp), file_name)
