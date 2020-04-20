from abc import abstractclassmethod
from typing import NamedTuple

from dateutil import parser


class FswatchEvent(NamedTuple):
    file_name: str
    timestamp: str

    @classmethod
    def coerce(cls, timestamp, file_name):
        timestamp = parser.parse(timestamp)
        return cls(str(timestamp), file_name)

    def __str__(self):
        return "{}, {}".format(self.file_name, self.timestamp)
