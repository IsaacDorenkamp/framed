import queue

from .event import Event

from .action import ActionEvent
from .change import ChangeEvent


_events: queue.Queue[Event] = queue.Queue()
def queue_event(event: Event):
    _events.put_nowait(event)


def process_events():
    while not _events.empty():
        event = _events.get()
        event.source._process(event)


__all__ = [
    "queue_event", "process_events",
    "Event", "ActionEvent", "ChangeEvent"
]

