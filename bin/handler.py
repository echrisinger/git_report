import os
from datetime import date
from abc import abstractmethod
from logging import getLogger
from typing import List, Type

import boto3
from gevent import monkey
from gevent.queue import Queue
from gevent.threading import Thread

from git_report.data_access import (injected_resources_context,
                                    SQSConsumer, GitEventDynamoDao, DynamoEventWriter, SQSProducer)

from git_report.events import Event, GitEvent, ReportRequestEvent
from git_report.exceptions import GitReportException
from git_report.threading import beat_queue, select

# TODO: figure out why this breaks SSL in boto3 Dynamo lib :(
# monkey.patch_all()

log = getLogger(__name__)
GIT_EVENT_BROKER_URL = os.environ.get('GIT_REPORT_GIT_EVENT_URL')
REPORT_EVENT_BROKER_URL = os.environ.get('GIT_REPORT_REPORT_EVENT_URL')
REPORT_BROKER_URL = os.environ.get('GIT_REPORT_REPORT_URL')

# TODO: put this in configuration file (YAML)
GIT_EVENT_TABLE_NAME = 'git_report_git_events'
REPORT_EVENT_TABLE_NAME = 'git_report_report_events'

GIT_EVENT_BEAT = 1
REPORT_EVENT_BEAT = 0.1


def log_failure_to_persist(event):
    err_msg = ",".join([
        getattr(f, event)
        for f in event._fields
    ])
    log.error('Failed to store event: {}'.format(err_msg))


class GitEventController:
    def __init__(self, consumer, dao):
        self.consumer = consumer
        self.dao = dao

    def query(self, date) -> List[GitEvent]:
        return self.dao.query(date)

    def get_event(self) -> GitEvent:
        return self.consumer.poll()

    def persist(self, event: GitEvent):
        return self.dao.persist(event)


class ReportRequestEventController:
    def __init__(self, consumer, dao):
        self.consumer = consumer
        self.dao = dao

    def get_event(self):
        return self.consumer.poll()

    def persist(self, event: ReportRequestEvent):
        return self.dao.persist(event)


def generate_report(events: List[GitEvent]):
    pass


if __name__ == "__main__":
    # TODO: all of this should be configured via a config file (YAML).
    git_event_queue = Queue(maxsize=None)
    Thread(target=beat_queue, args=(git_event_queue, GIT_EVENT_BEAT)).start()

    report_event_queue = Queue(maxsize=None)
    Thread(target=beat_queue, args=(report_event_queue, REPORT_EVENT_BEAT)).start()

    with injected_resources_context(
        dynamo=boto3.client('dynamodb'),
        sqs=boto3.client('sqs')
    ):
        git_event_controller = GitEventController(
            consumer=SQSConsumer(GIT_EVENT_BROKER_URL, GitEvent),
            dao=GitEventDynamoDao(GIT_EVENT_TABLE_NAME)
        )

        report_event_controller = ReportRequestEventController(
            consumer=SQSConsumer(REPORT_EVENT_BROKER_URL, ReportRequestEvent),
            dao=DynamoEventWriter(REPORT_EVENT_TABLE_NAME)
        )

        report_producer = SQSProducer(REPORT_BROKER_URL)

        for which, item in select(git_event_queue, report_event_queue):
            if which is git_event_queue:
                event = git_event_controller.get_event()

                if event:
                    persisted = git_event_controller.persist(event)
                    if not persisted:
                        log_failure_to_persist(event)

            elif which is report_event_queue:
                report_event = report_event_controller.get_event()
                if event:
                    persisted = report_event_controller.persist(report_event)
                    if not persisted:
                        log_failure_to_persist(report_event)

                    git_events = git_event_controller.query(
                        report_event.report_date
                    )

                    report = generate_report(report_event, git_events)
                    producer.notify(report)

                    # producer.send(report) TODO
