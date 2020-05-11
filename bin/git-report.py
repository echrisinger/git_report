#!/usr/bin/env python3

import argparse
import datetime
import os
import sys
import time
from logging import DEBUG, StreamHandler, getLogger
from pprint import pformat

import boto3
from git_report.data_access import (ComplexEventSerializer, SQSEventProducer,
                                    SQSRawConsumer)
from git_report.display_logs import (GitEventHandler, RepositoryWatchRegistry,
                                     SQSMetricsObserver)
from git_report.events import ReportGeneratedEvent, ReportRequestedEvent
from git_report.repo import find_all_root_repos
from pyfiglet import figlet_format
from watchdog.observers.polling import PollingObserver

log = getLogger(__name__)

GIT_EVENT_QUEUE_URL = os.environ.get('GIT_REPORT_GIT_EVENT_URL')
REPORT_REQUESTED_QUEUE_URL = os.environ.get('GIT_REPORT_REPORT_REQUESTED_EVENT_URL')
GIT_REPORT_REPORT_URL = os.environ.get('GIT_REPORT_REPORT_URL')

REPORT_POLLING_INTERVAL = 0.1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--observe-path",
        type=str,
        default=None
    )
    parser.add_argument(
        "--request-report",
        action='store_true',
        default=False
    )
    parser.add_argument(
        "--report-date",
        type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(),
        default=datetime.datetime.now().date()
    )
    parser.add_argument(
        "--stdout",
        action='store_true',
        default=False
    )

    args = parser.parse_args()

    if args.stdout:
        handler = StreamHandler(sys.stdout)
        handler.setLevel(DEBUG)
        log.addHandler(handler)

    sqs = boto3.client('sqs')
    if args.observe_path:
        repo_paths = find_all_root_repos(args.observe_path)
        event_handler = GitEventHandler(observers=[SQSMetricsObserver(sqs, GIT_EVENT_QUEUE_URL)])
        observer = PollingObserver()

        for path in repo_paths:
            log.warning('Observing git repo: {}'.format(path))
            watch = observer.schedule(event_handler, path, recursive=True)
            RepositoryWatchRegistry.register(watch)

        try:
            observer.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.warning('Shutdown: Stopping observer due to interrupt. Please wait.')

        try:
            observer.stop()
            observer.join()
        except RuntimeError:
            # if exiting early enough, and thread hasn't started.
            pass
    elif args.request_report:
        event = ReportRequestedEvent.coerce(args.report_date, datetime.datetime.now())
        producer = SQSEventProducer(sqs, REPORT_REQUESTED_QUEUE_URL)
        producer.notify(event)

        poll_count = 10 / REPORT_POLLING_INTERVAL
        raw_body = None

        consumer = SQSRawConsumer(sqs, GIT_REPORT_REPORT_URL)
        while poll_count and not raw_body:
            poll_count -= 1
            raw_body = consumer.poll()

        ascii_header = figlet_format('Git Report')
        print(ascii_header)

        formatted_aggregations = pformat(raw_body['aggregations']['file_aggregations'])
        formatted_timeline = pformat(raw_body['timelines']['total_timeline'])
        git_report = """

        Counts:
        {aggregations}

        Timeline:
        {timeline}
        """.format(
            ascii_header=ascii_header,
            aggregations=formatted_aggregations,
            timeline=formatted_timeline
        )
        print(git_report)
