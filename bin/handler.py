import os
from datetime import datetime
from logging import getLogger

import boto3
from botocore.exceptions import ClientError
from gevent.monkey import patch_all
from gevent.queue import Queue
from gevent.threading import Thread

from git_report.events import FswatchEvent
from git_report.exceptions import GitReportException
from git_report.utils import beat_queue, select

patch_all()


log = getLogger(__name__)
BROKER_URL = os.environ.get('GIT_REPORT_BROKER_URL')
FSWATCH_BEAT = 1


class FswatchEventController:
    # TODO: needs to be abstracted to implementation for Fswatch.
    # Refactor SQS consumer to be abstracted away from FswatchEvent
    def __init__(self, consumer, mapper):
        self.consumer = consumer
        self.mapper = mapper

    def get_event(self) -> FswatchEvent:
        return self.consumer.poll()

    def persist(self, event: FswatchEvent):
        # TODO: implement me
        return self.mapper.persist(event)


# TODO: make this via a class factory
class SQSConsumer:
    def __init__(self, broker_url):
        self.broker_url = broker_url

    def poll(self):
        # Create SQS client
        sqs = boto3.client('sqs')

        # Receive message from SQS queue
        response = sqs.receive_message(
            QueueUrl=BROKER_URL,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            MessageAttributeNames=list(FswatchEvent._fields),
            WaitTimeSeconds=0,
        )

        res = None
        if 'Messages' in response:
            msg = response['Messages'][0]['MessageAttributes']
            res = FswatchEvent.coerce(
                **{
                    field: msg[field]['StringValue']
                    for field in FswatchEvent._fields
                }
            )
        return res


class FailedToPersistError(GitReportException):
    pass


class DynamoMapper:
    # TODO: organize this a little more. formalize enhancement of events into separate layer.
    def __init__(self, event_cls):
        self.event_cls = event_cls

    def persist(self, event):
        dynamo = boto3.client('dynamodb')
        event_entries = {
            f: {'S': getattr(event, f)}
            for f in event._fields
        }
        date = datetime.parse(event.timestamp).date()
        dynamo_item = {
            'date': {'S': str(date)},
            **event_entries
        }
        try:
            dynamo.put_item(
                TableName='git_report_fswatch_events',
                Item=dynamo_item
            )
        except ClientError as e:
            raise FailedToPersistError(e) from e

        return True


if __name__ == "__main__":
    fswatch_event_queue = Queue(maxsize=None)
    Thread(target=beat_queue, args=(fswatch_event_queue, FSWATCH_BEAT)).start()

    for which, _ in select(fswatch_event_queue):
        if which is fswatch_event_queue:
            controller = FswatchEventController(
                consumer=SQSConsumer(BROKER_URL),
                mapper=DynamoMapper(FswatchEvent)
            )
            event = controller.get_event()
            persisted = controller.persist(event)
            if not persisted:
                err_msg = ",".join([
                    getattr(f, event)
                    for f in event._fields
                ])
                log.error('Failed to store event: {}'.format(err_msg))
