import os
from logging import getLogger

import boto3
from botocore.exceptions import ClientError
from dateutil import parser
from gevent import monkey
from gevent.queue import Queue
from gevent.threading import Thread

from git_report.events import FswatchEvent
from git_report.exceptions import GitReportException
from git_report.utils import beat_queue, select

# TODO: figure out why this breaks SSL in boto3 Dynamo lib :(
# monkey.patch_all()

log = getLogger(__name__)
BROKER_URL = os.environ.get('GIT_REPORT_BROKER_URL')
FSWATCH_BEAT = 1


class FswatchEventController:
    # TODO: needs to be abstracted to implementation for Fswatch.
    # Refactor SQS consumer to be abstracted away from FswatchEvent
    def __init__(self, consumer, dao):
        self.consumer = consumer
        self.dao = dao

    def get_event(self) -> FswatchEvent:
        return self.consumer.poll()

    def persist(self, event: FswatchEvent):
        return self.dao.persist(event)


# TODO: make this via a class factory
class FswatchEventSQSConsumer:
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
        receipt_handle = None
        if 'Messages' in response:
            receipt_handle = response['Messages'][0]['ReceiptHandle']
            msg = response['Messages'][0]['MessageAttributes']
            res = FswatchEvent.coerce(
                **{
                    field: msg[field]['StringValue']
                    for field in FswatchEvent._fields
                }
            )

            try:
                sqs.delete_message(
                    QueueUrl=BROKER_URL,
                    ReceiptHandle=receipt_handle
                )
            except ClientError:
                log.error(
                    'Failed to delete event from SQS: {}'
                    .format(receipt_handle)
                )
        return res


class FailedToPersistError(GitReportException):
    pass


class FswatchEventDynamoDao:
    # TODO:
    # Organize this a little more. formalize enhancement of
    # events into separate controller method.
    # Make this accept a different object, which has property
    # decorators for each field it wants to look up

    def persist(self, event: FswatchEvent):
        dynamo = boto3.client('dynamodb')
        event_entries = {
            f: {'S': getattr(event, f)}
            for f in event._fields
        }

        date = parser.parse(event.timestamp).date()
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

    for which, item in select(fswatch_event_queue):
        if which is fswatch_event_queue:
            controller = FswatchEventController(
                consumer=FswatchEventSQSConsumer(BROKER_URL),
                dao=FswatchEventDynamoDao()
            )
            event = controller.get_event()
            if event:
                persisted = controller.persist(event)

                if not persisted:
                    err_msg = ",".join([
                        getattr(f, event)
                        for f in event._fields
                    ])
                    log.error('Failed to store event: {}'.format(err_msg))
