from contextlib import contextmanager
from datetime import date
from dateutil import parser
from logging import getLogger
from typing import List, Type

from botocore.exceptions import ClientError

from git_report.events import (Event, GitEvent, ReportRequestEvent,
                               ReportResponseEvent)
from git_report.exceptions import GitReportException

log = getLogger(__name__)


@contextmanager
def injected_resources_context(**resources):
    # a nice pattern, via Cameron.
    for key, value in resources.items():
        globals()[key] = value

    yield

    for key in resources:
        del globals()[key]


class SQSConsumer:
    def __init__(self, broker_url, event_class: Type[Event]):
        self.broker_url = broker_url
        self.event_class = event_class

    def poll(self):
        # Receive message from SQS queue
        response = sqs.receive_message(
            QueueUrl=self.broker_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            MessageAttributeNames=list(self.event_class._fields),
            WaitTimeSeconds=0,
        )

        res = None
        receipt_handle = None
        if 'Messages' in response:
            receipt_handle = response['Messages'][0]['ReceiptHandle']
            msg = response['Messages'][0]['MessageAttributes']
            res = self.event_class.coerce(
                **{
                    field: msg[field]['StringValue']
                    for field in self.event_class._fields
                }
            )

            try:
                sqs.delete_message(
                    QueueUrl=self.broker_url,
                    ReceiptHandle=receipt_handle
                )
            except ClientError:
                log.error(
                    'Failed to delete event from SQS: {}'
                    .format(receipt_handle)
                )
        return res


class ReportSQSProducer:
    def __init__(self, broker_url):
        self.broker_url = broker_url

    def notify(self, report_response_event):
        pass
        # Send message to SQS queue
        # response = sqs.send_message(
        #     QueueUrl=self.broker_url,
        #     MessageAttributes={
        #         field: {
        #             'DataType': 'String',
        #             'StringValue': getattr(formatted_event, field)
        #         } for field in formatted_event._fields
        #     },
        #     MessageBody=str(formatted_event)
        # )

        # if 'MessageId' in response:
        #     log.info('Sent Message, ID: {}, Event: {}'.format(response['MessageId'], formatted_event))
        # else:
        #     log.error('Failed to send message: {}'.format(formatted_event))


class FailedToPersistError(GitReportException):
    pass


class DynamoEventWriter:
    def __init__(self, table_name):
        self.table_name = table_name

    def persist(self, event: Event, **kwargs):
        event_entries = {
            f: {'S': getattr(event, f)}
            for f in event._fields
        }

        dynamo_item = {
            **event_entries,
            **{
                key: {'S': str(val)}
                for key, val in kwargs.items()
            },
        }

        try:
            dynamo.put_item(
                TableName=self.table_name,
                Item=dynamo_item
            )
        except ClientError as e:
            raise FailedToPersistError(e) from e

        return True


class GitEventDynamoDao:
    def __init__(self, table_name):
        self.table_name = table_name
        self.event_writer = DynamoEventWriter(self.table_name)

    def persist(self, event: GitEvent) -> bool:
        date = parser.parse(event.timestamp).date()
        return self.event_writer.persist(event, date=date)

    def query(self, date: date) -> List[GitEvent]:
        response = dynamo.query(
            TableName=self.table_name,
            KeyConditionExpression='date = :date',
            ExpressionAttributeValues={
                ':date': {'S': str(date)}
            }
        )

        res = []
        if 'Items' in response:
            def constructor_args(item):
                return [
                    getattr(f, item)
                    for f in GitEvent._fields
                ]

            res = [
                GitEvent(*constructor_args(item))
                for item in response['Items']
            ]
        return res
