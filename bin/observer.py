import argparse
import time
import os
import sys
from logging import DEBUG, StreamHandler, getLogger

from watchdog.observers.polling import PollingObserver

from git_report.display_logs import (GitEventHandler, RepositoryWatchRegistry,
                                     SQSMetricsObserver)
from git_report.repo import find_all_root_repos

log = getLogger(__name__)

BROKER_URL = os.environ.get('GIT_REPORT_BROKER_URL')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root_path",
        type=str
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

    repo_paths = find_all_root_repos(args.root_path)
    event_handler = GitEventHandler(observers=[SQSMetricsObserver(BROKER_URL)])
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
