from typing import NamedTuple, List

from datetime import timedelta
from dateutil import parser

Event = SubEvent = NamedTuple

# Event => something that is sent via a message broker.
# SubEvent => serialized inside an Event.

# TODO: when these schemas start to change, put them into a more
# formalized schema, a la protocol buffers or avro.


class GitEvent(Event):
    file_name: str
    timestamp: str

    @classmethod
    def coerce(cls, file_name, timestamp):
        timestamp = parser.parse(timestamp)
        return cls(file_name, str(timestamp))


class ReportRequestedEvent(Event):
    report_date: str
    timestamp: str

    @classmethod
    def coerce(cls, report_date, timestamp):
        return cls(str(report_date), str(timestamp))


class ReportTimelineEvent(SubEvent):
    file_name: str
    # parse with pytimeparse.timeparse:
    # https://stackoverflow.com/questions/4628122/how-to-construct-a-timedelta-object-from-a-simple-string
    duration: timedelta


class ReportTotalTimeline(SubEvent):
    # tracking all files across all projects
    timeline_event: List[ReportTimelineEvent]


class ReportTimelines(SubEvent):
    total_timeline: ReportTotalTimeline


class ReportFileAggregation(SubEvent):
    file_name: str
    duration: timedelta
    count: int


class ReportAggregations(SubEvent):
    file_aggregations: List[ReportFileAggregation]


class ReportGeneratedEvent(Event):
    uuid: str
    timelines: ReportTimelines
    aggregations: ReportAggregations
