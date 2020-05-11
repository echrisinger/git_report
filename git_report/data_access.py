import json
from contextlib import contextmanager
from datetime import date
from logging import getLogger
from numbers import Number
from typing import List, Type

from botocore.exceptions import ClientError
from dateutil import parser
from git_report.events import (Event, GitEvent, ReportGeneratedEvent,
                               ReportRequestedEvent)
from git_report.exceptions import GitReportException

log = getLogger(__name__)


def coerce(value):
    """
    Try to convert to a primitive JSON type
    (not array, object) or just nullify
    """
    res = None
    if any([
        isinstance(value, t)
        for t in [int, str, bool]
    ]):
        res = value
    elif isinstance(value, Number):
        res = float(value)
    else:
        try:
            res = str(value)
        except:
            res = None
    return res


class ComplexEventSerializer:
    @classmethod
    def serialize(cls, event):
        is_namedtuple = False
        try:
            getattr(event, '_fields')
            is_namedtuple = True
        except AttributeError:
            pass

        if isinstance(event, list):
            return [
                cls.serialize(item)
                for item in event
            ]
        elif isinstance(event, dict):
            raise "Unexpected type -- shouldn't need to be supported"
        elif not is_namedtuple:
            return coerce(event)

        return {
            field: cls.serialize(getattr(event, field))
            for field in event._fields
        }

    @classmethod
    def deserialize(self, raw_event):
        pass


class SQSConsumer:
    # TODO: instead of this, just pass the event_class to be parsed.
    def __init__(self, sqs, broker_url, event_class: Type[Event]):
        self.sqs = sqs
        self.broker_url = broker_url
        self.event_class = event_class

    def poll(self):
        # Receive message from SQS queue
        response = self.sqs.receive_message(
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
            coerce_args = {}
            for field in self.event_class._fields:
                coerce_args[field] = msg[field]['StringValue']

            res = self.event_class.coerce(**coerce_args)

            try:
                self.sqs.delete_message(
                    QueueUrl=self.broker_url,
                    ReceiptHandle=receipt_handle
                )
            except ClientError:
                log.error(
                    'Failed to delete event from SQS: {}'
                    .format(receipt_handle)
                )
        return res


class SQSEventProducer:
    def __init__(self, sqs, broker_url):
        self.sqs = sqs
        self.broker_url = broker_url

    def notify(self, event: Event):
        response = self.sqs.send_message(
            QueueUrl=self.broker_url,
            MessageAttributes={
                field: {
                    'DataType': 'String',
                    'StringValue': getattr(event, field)
                } for field in event._fields
            },
            MessageBody=str(event)
        )

        if 'MessageId' in response:
            log.info('Sent Message, ID: {}, Event: {}'.format(response['MessageId'], event))
        else:
            log.error('Failed to send message: {}'.format(event))


class SQSRawProducer:
    def __init__(self, sqs, broker_url):
        self.sqs = sqs
        self.broker_url = broker_url

    def notify(self, json_like):
        response = self.sqs.send_message(
            QueueUrl=self.broker_url,
            MessageBody=json.dumps(json_like)
        )

        if 'MessageId' in response:
            log.info('Sent Message, ID: {}, Event: {}'.format(response['MessageId'], json_like))
        else:
            log.error('Failed to send message: {}'.format(json_like))


class FailedToPersistError(GitReportException):
    pass


class DynamoEventWriter:
    def __init__(self, dynamo, table_name):
        self.dynamo = dynamo
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
            self.dynamo.put_item(
                TableName=self.table_name,
                Item=dynamo_item
            )
        except ClientError as e:
            raise FailedToPersistError(e) from e

        return True


class GitEventDynamoDao:
    def __init__(self, dynamo, table_name):
        self.dynamo = dynamo
        self.table_name = table_name
        self.event_writer = DynamoEventWriter(self.dynamo, self.table_name)

    def persist(self, event: GitEvent) -> bool:
        date = parser.parse(event.timestamp).date()
        return self.event_writer.persist(event, date=date)

    def query(self, date: date) -> List[GitEvent]:
        response = self.dynamo.query(
            TableName=self.table_name,
            KeyConditionExpression='#date = :date',
            ExpressionAttributeNames={"#date": "date"},
            ExpressionAttributeValues={
                ':date': {'S': str(date)}
            }
        )

        def kwargs(item):
            return {
                f: item[f]['S']
                for f in GitEvent._fields
            }
        return [
            GitEvent.coerce(**kwargs(event))
            for event in response['Items']
        ]
