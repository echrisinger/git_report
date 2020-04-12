from typing import List

from gevent import sleep
from gevent.queue import Queue, Empty


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
