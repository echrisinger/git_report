from typing import NamedTuple, List

from dateutil import parser

Event = SubEvent = NamedTuple

# Event => something that is sent via a message broker.
# SubEvent => serialized inside an Event.


class GitEvent(Event):
    file_name: str
    timestamp: str

    @classmethod
    def coerce(cls, timestamp, file_name):
        timestamp = parser.parse(timestamp)
        return cls(str(timestamp), file_name)


class ReportRequestEvent(Event):
    report_date: str
    timestamp: str

    @classmethod
    def coerce(cls, report_date, timestamp):
        report_date = parser.parse(report_date).date()
        timestamp = parser.parse(timestamp)
        return cls(str(report_date), str(timestamp))


class ReportTotalTimeline(SubEvent):
    pass


class ReportTimelines(SubEvent):
    total_timeline: ReportTotalTimeline


class ReportTimeAggregation(SubEvent):
    pass


class ReportCountAggregation(SubEvent):
    pass


class ReportAggregations(SubEvent):
    time_aggregations: List[ReportTimeAggregation]
    count_aggregations: List[ReportCountAggregation]


class ReportResponseEvent(Event):
    timelines: ReportTimelines
    aggregations: ReportAggregations

    # project_time_aggregation: ReportProjectTimeAggregation -- TODO: in the future.
    # projects: ReportProjects
