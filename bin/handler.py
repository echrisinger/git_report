#!/usr/bin/env python3

import os
from abc import abstractmethod
from collections import defaultdict
from dateutil.parser import parse
from datetime import date, timedelta
from logging import getLogger
from typing import List, Type, Mapping
from uuid import uuid1, UUID
from methodtools import lru_cache

import boto3
from gevent import monkey
from gevent.queue import Queue
from gevent.threading import Thread
from git_report.data_access import (ComplexEventSerializer,
                                    DynamoEventWriter,
                                    GitEventDynamoDao,
                                    SQSConsumer,
                                    SQSRawProducer)

from git_report.events import (
    Event,
    GitEvent,
    ReportRequestedEvent,
    ReportGeneratedEvent,
    ReportAggregations,
    ReportFileAggregation,
    ReportTimelines,
    ReportTotalTimeline,
    ReportTimelineEvent,
)
from git_report.exceptions import GitReportException
from git_report.report import ReportFactory
from git_report.threading import beat_queue, select

# TODO: figure out why this breaks SSL in boto3 Dynamo lib :(
# monkey.patch_all()

log = getLogger(__name__)
GIT_EVENT_QUEUE_URL = os.environ.get('GIT_REPORT_GIT_EVENT_URL')
REPORT_REQUESTED_QUEUE_URL = os.environ.get('GIT_REPORT_REPORT_REQUESTED_EVENT_URL')
REPORT_QUEUE_URL = os.environ.get('GIT_REPORT_REPORT_URL')

# TODO: put this in configuration file (YAML)
GIT_EVENT_TABLE_NAME = 'git_report_git_events'
REPORT_REQUESTED_EVENT_TABLE_NAME = 'git_report_report_requested_events'
REPORTS_TABLE_NAME = 'git_report_reports'

GIT_EVENT_BEAT = 1
REPORT_EVENT_BEAT = 0.1


def log_failure_to_persist_event(event: Event):
    err_msg = ",".join([
        getattr(f, event)
        for f in event._fields
    ])
    log.error('Failed to persist event: {}'.format(err_msg))

# TODO: These controllers should get their own file structure, probably.


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


class ReportRequestedEventController:
    def __init__(self, consumer, dao):
        self.consumer = consumer
        self.dao = dao

    def get_event(self):
        return self.consumer.poll()

    def persist(self, event: ReportRequestedEvent):
        return self.dao.persist(event)


class ReportController:
    def __init__(self, report_factory, dao, producer):
        self.report_factory = report_factory
        self.dao = dao
        self.producer = producer

    # TODO ReportGeneratedEvent => Report, and ReportGeneratedEvent should be
    # created in notify via a "serializer"
    def create_report(
        self,
        uuid: UUID,
        report_requested_event: ReportRequestedEvent,
        git_events: List[GitEvent]
    ) -> ReportGeneratedEvent:
        return self.report_factory.create_report(uuid, report_requested_event, git_events)

    def persist(self, report: ReportGeneratedEvent) -> bool:
        return self.dao.persist(report)

    def notify(self, report: ReportGeneratedEvent) -> bool:
        return self.producer.notify(report)


# TODO: all of this should be configured via a config file (YAML).
if __name__ == "__main__":
    git_event_queue = Queue(maxsize=None)
    Thread(target=beat_queue, args=(git_event_queue, GIT_EVENT_BEAT)).start()

    report_event_queue = Queue(maxsize=None)
    Thread(target=beat_queue, args=(report_event_queue, REPORT_EVENT_BEAT)).start()

    dynamo = boto3.client('dynamodb')
    sqs = boto3.client('sqs')

    git_event_controller = GitEventController(
        consumer=SQSConsumer(sqs, GIT_EVENT_QUEUE_URL, GitEvent),
        dao=GitEventDynamoDao(dynamo, GIT_EVENT_TABLE_NAME)
    )

    report_requested_events_controller = ReportRequestedEventController(
        consumer=SQSConsumer(sqs, REPORT_REQUESTED_QUEUE_URL, ReportRequestedEvent),
        dao=DynamoEventWriter(dynamo, REPORT_REQUESTED_EVENT_TABLE_NAME)
    )

    report_controller = ReportController(
        report_factory=ReportFactory(),
        dao=DynamoEventWriter(dynamo, REPORTS_TABLE_NAME),
        producer=SQSRawProducer(sqs, REPORT_QUEUE_URL)
    )

    for which, item in select(git_event_queue, report_event_queue):
        if which is git_event_queue:
            git_event = git_event_controller.get_event()

            if git_event:
                persisted = git_event_controller.persist(git_event)
                if not persisted:
                    log_failure_to_persist_event(git_event)

        elif which is report_event_queue:
            report_requested_event = report_requested_events_controller.get_event()
            if report_requested_event:
                uuid = str(uuid1())
                request_persisted = report_requested_events_controller.persist(
                    report_requested_event
                )
                if not request_persisted:
                    log_failure_to_persist_event(report_requested_event)

                git_events = git_event_controller.query(
                    report_requested_event.report_date
                )

                report = report_controller.create_report(
                    uuid,
                    report_requested_event,
                    git_events
                )
                # TODO: need to serialize Report/ReportGeneratedEvent
                # report_persisted = report_controller.persist(report)
                # if not report_persisted:
                #     log.warn("failed to persist report for {}".format(str(uuid)))
                breakpoint()
                serialized_report = ComplexEventSerializer.serialize(report)
                report_controller.notify(serialized_report)
