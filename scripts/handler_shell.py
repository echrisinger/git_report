import IPython
import os

from git_report.events import FswatchEvent
from git_report.display_logs import FswatchAdapter, RegexParser, ISO8601_EVENT_REGEX, SQSMetricsObserver
import boto3
from datetime import datetime
from pytz import timezone

BROKER_URL = os.environ.get('GIT_REPORT_BROKER_URL')


def get_event():
    return ' '.join([
        datetime.now().replace(tzinfo=timezone('EST')).
        strftime('%F %T %z'),
        'test2.abc'
    ])


def enqueue_test_message():
    event = get_event()
    adapter = FswatchAdapter(
        parser=RegexParser(ISO8601_EVENT_REGEX, FswatchEvent),
        observers=[SQSMetricsObserver(BROKER_URL)],
    )
    adapter.publish(event)


def get_fswatch_event() -> FswatchEvent:
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


if __name__ == "__main__":
    IPython.embed()
