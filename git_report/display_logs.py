import argparse
import re

from datetime import datetime
from dateutil.parser import parse as parse_datetime
from typing import (
    NamedTuple,
    List,
    Tuple,
)

from exceptions import GitReportException

# TODO: Replace the latter group with a valid expression to match all valid files.
# Otherwise will break for a subset of files.
ISO8601_EVENT_REGEX = r'^([\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2} [-,+][\d]{4}) ([/.-_a-zA-Z0-9]+)'
BROKER_URL = ''

class ParserError(GitReportException):
    pass

class FswatchEvent(NamedTuple):
    timestamp: datetime
    file_name: str

class FswatchListener:
    """
    Responsible for taking an unstructured log, output by
    a listening program, on the display logging file,
    and formatting into metadata such as date and text,
    that can be parsed by listeners
    """
    def __init__(self, parser, listeners: List):
        self.parser = parser
        self.listeners = listeners

    def handle(self, event: str):
        formatted_event = self.parse_event(event)
        for l in self.listeners:
            l.notify(formatted_event)

    def parse_event(self, event: str) -> FswatchEvent:
        return self.parser.parse(event)

class RegexParser:
    """
    Responsible for parsing logs, using a regex.
    """
    def __init__(self, regex: str):
        self.regex = re.compile(regex)

    def parse(self, event: str) -> FswatchEvent:
        # Probably a better way to do this
        match = self.regex.match(event)
        if not match:
            raise ParserError(
                "Could not parse: {}".format(event)
            )
        groups = match.groups()
        if len(groups) != 2:
            raise ParserError(
                "Could not parse: {}".format(event)
            )
        ts, file_name = groups
        dt = parse_datetime(ts)
        return FswatchEvent(dt, file_name)

class SimpleBroker:
    """
    Listens to structured logs, and publishes records to
    brokers as deemed relevant.
    """
    def __init__(self, broker_url):
        self.broker_url = broker_url

    def notify(self, event: FswatchEvent):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "log",
        type=str
    )
    args = parser.parse_args()
    handler = FswatchListener(
        parser=RegexParser(ISO8601_EVENT_REGEX),
        listeners=[SimpleBroker(BROKER_URL)]
    )
    handler.handle(args.log)
