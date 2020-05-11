from dateutil.parser import parse
from datetime import timedelta
from methodtools import lru_cache
from typing import List, Mapping

from git_report.events import (GitEvent, ReportAggregations,
                               ReportFileAggregation, ReportGeneratedEvent,
                               ReportRequestedEvent, ReportTimelineEvent,
                               ReportTimelines, ReportTotalTimeline)


class ReportFactory:
    def create_report(self, uuid, report_requested_event, git_events) -> ReportGeneratedEvent:
        def sort_key(event: GitEvent): return (event.timestamp, event.file_name)
        sorted_events = sorted(git_events, key=sort_key)  # TODO: this can be done in Dynamo

        timelines = self._build_timelines(sorted_events)
        aggregations = self._build_aggregations(sorted_events)

        return ReportGeneratedEvent(uuid, timelines, aggregations)

    def _build_timelines(self, git_events) -> ReportTimelines:
        total_timeline = self._build_total_timeline(git_events)
        return ReportTimelines(total_timeline)

    def _build_total_timeline(self, git_events) -> ReportTotalTimeline:
        if not git_events:
            return []

        prev_timestamp = parse(git_events[0].timestamp)

        total_timeline = []
        for event in git_events:
            curr_timestamp = parse(event.timestamp)
            duration = curr_timestamp - prev_timestamp
            timeline_event = ReportTimelineEvent(event.file_name, duration)
            total_timeline.append(timeline_event)

        return total_timeline

    def _build_aggregations(self, git_events) -> ReportAggregations:
        file_aggregations = self._build_file_aggregations(git_events)
        return ReportAggregations(file_aggregations)

    def _build_file_aggregations(self, git_events) -> List[ReportFileAggregation]:
        total_timeline = self._build_total_timeline(git_events)

        def sort_key(timeline_event: ReportTimelineEvent):
            return timeline_event.file_name
        file_sorted_timeline = sorted(total_timeline, key=sort_key)

        file_aggregations: Mapping[str, ReportFileAggregation] = {}
        for event in file_sorted_timeline:
            if event.file_name not in file_aggregations:
                file_aggregations[event.file_name] = ReportFileAggregation(timedelta(0), 0)

            aggregation = file_aggregations[event.file_name]
            aggregation.count += 1
            aggregation.duration += event.duration

        return sorted(file_aggregations.values())
