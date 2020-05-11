import os
from datetime import datetime
from logging import getLogger
from typing import List, NamedTuple

import boto3
from watchdog.events import FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers.api import ObservedWatch

from git_report.events import GitEvent
from git_report.repo import is_file_ignored
from git_report.time import local_time
from git_report.strings import get_matching_entry

log = getLogger(__name__)


class RepositoryWatchRegistry(object):
    """
    Keeps track of observed git repositories, so we don't have to requery
    the file system tree repetitively.
    """
    entries: List[ObservedWatch] = []

    @classmethod
    def register(cls, watch):
        cls.entries.append(watch)


class GitEventHandler(FileSystemEventHandler):
    def __init__(self, observers, *args, **kwargs):
        super(GitEventHandler, self).__init__(*args, **kwargs)
        self.observers = observers

    def on_moved(self, event: FileSystemMovedEvent):
        now = local_time()
        self._add_event(event.src_path, now)

        if self._is_file_in_source_control(event.dest_path):
            self._add_event(event.dest_path, now)

    def on_any_event(self, event):
        self._add_event(event.src_path)

    def _is_file_in_source_control(self, path):
        # first check if it is in a repository,
        # and then ls the smaller active subtree
        # to see if it is actually tracked by source control of the repo.
        # TODO: Just apply the .gitignore regexes to the string directly

        tracked_repo = get_matching_entry(
            [entry.path for entry in RepositoryWatchRegistry.entries],
            path
        )
        return tracked_repo and not is_file_ignored(path)

    def _add_event(self, path, timestamp=None):
        if not timestamp:
            timestamp = local_time()

        event = GitEvent(path, timestamp.isoformat())
        for observer in self.observers:
            observer.notify(event)


class SQSMetricsObserver(object):
    """
    Listens to structured logs, and publishes records to SQS broker.
    """

    def __init__(self, sqs, broker_url):
        self.sqs = sqs
        self.broker_url = broker_url

    def notify(self, formatted_event: NamedTuple) -> None:
        # Create SQS client

        # Send message to SQS queue
        response = self.sqs.send_message(
            QueueUrl=self.broker_url,
            MessageAttributes={
                field: {
                    'DataType': 'String',
                    'StringValue': getattr(formatted_event, field)
                } for field in formatted_event._fields
            },
            MessageBody=str(formatted_event)
        )

        if 'MessageId' in response:
            log.info('Sent Message, ID: {}, Event: {}'.format(response['MessageId'], formatted_event))
        else:
            log.error('Failed to send message: {}'.format(formatted_event))
