from typing import List

from gevent import sleep
from gevent.queue import Queue, Empty

import re

# TODO split this into separate modules


def beat_queue(queue, beat_seconds):
    while True:
        queue.put(True)
        sleep(beat_seconds)


def select(*queues: List[Queue]):
    while True:
        which, item = None, None
        for queue in queues:
            try:
                item = queue.get(block=None)
                which = queue
            except Empty:
                pass

        yield which, item
        sleep(0)


def get_matching_entry(entries: List[str], path):
    def wildcard_postfix(s): return r"{}*".format(s)
    return next(iter([
        e
        for e in entries
        if re.search(wildcard_postfix(e), path)
    ]), None)
