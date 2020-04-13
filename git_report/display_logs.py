import argparse
import os
import re
from datetime import datetime
from logging import getLogger
from typing import List, NamedTuple, Tuple, Type, Union

import boto3
from dateutil.parser import parse as parse_datetime
from watchdog.events import FileSystemMovedEvent, RegexMatchingEventHandler

from git_report.exceptions import GitReportException
from git_report.git import find_all_root_repos, get_versioned_files

log = getLogger(__name__)

# TODO: Replace the latter group with a valid expression to match all valid files.
# Otherwise will break for a subset of files.
BROKER_URL = os.environ.get('GIT_REPORT_BROKER_URL')
ISO8601_EVENT_REGEX = r'^([\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2} [-,+][\d]{4}) ([/.-_a-zA-Z0-9]+)'


class GitEventHandler(RegexMatchingEventHandler):
    def on_moved(event: FileSystemMovedEvent):
        # TODO: use ._dest_path, .src_path to emit events for both directories,
        # with dest path coming after src_path.
        self._add_event(event.src_path)
        self._add_event(event._dest_path)

    def on_any_event(event):
        self._add_event(event.src_path)

    def _add_src_event(event):
        # TODO: check if file is in active source control via get_versioned_files
        pass


class ParserError(GitReportException):
    pass


class FswatchEvent(NamedTuple):
    timestamp: str
    file_name: str

    @classmethod
    def coerce(cls, timestamp: str, file_name: str):
        dt = parse_datetime(timestamp).isoformat()
        return cls(dt, file_name)


class FswatchAdapter:
    """
    Responsible for taking an unstructured log, output by
    a listening program, on the display logging file,
    and formatting into metadata such as date and text,
    that can be parsed by observers.
    """

    def __init__(self, parser, observers: List):
        self.parser = parser
        self.observers = observers

    def publish(self, event: str):
        formatted_event = self.parse_event(event)
        for l in self.observers:
            l.notify(formatted_event, event)

    def parse_event(self, event: str) -> FswatchEvent:
        return self.parser.parse(event)


class RegexParser:
    """
    Responsible for parsing logs, using a regex, into a structured type.
    """

    def __init__(self, regex: str, event_cls: Type[NamedTuple]):
        self.regex = re.compile(regex)
        self.event_cls = event_cls

    def parse(self, event: str) -> NamedTuple:
        # Probably a better way to do this
        # Could make this type more specific.
        match = self.regex.match(event)
        if not match:
            raise ParserError(
                "Could not parse: {}".format(event)
            )
        groups = match.groups()
        if len(groups) != len(self.event_cls._fields):
            raise ParserError(
                "Could not parse: {}".format(event)
            )
        return self.event_cls.coerce(*groups)


class SQSMetricsObserver:
    """
    Listens to structured logs, and publishes records to
    brokers as deemed relevant.
    """

    def __init__(self, broker_url):
        self.broker_url = broker_url

    def notify(self, formatted_event: NamedTuple, event: str) -> None:
        # Create SQS client
        sqs = boto3.client('sqs')

        # Send message to SQS queue
        response = sqs.send_message(
            QueueUrl=self.broker_url,
            MessageAttributes={
                field: {
                    'DataType': 'String',
                    'StringValue': getattr(formatted_event, field)
                } for field in formatted_event._fields
            },
            MessageBody=event
        )
        if 'MessageId' in response:
            log.info('Sent Message, ID: {}, Event: {}'.format(response['MessageId'], event))
        else:
            log.error('Failed to send message: {}'.format(event))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "log",
        type=str
    )
    args = parser.parse_args()
    adapter = FswatchAdapter(
        parser=RegexParser(ISO8601_EVENT_REGEX, FswatchEvent),
        observers=[SQSMetricsObserver(BROKER_URL)],
    )
    adapter.publish(args.log)
