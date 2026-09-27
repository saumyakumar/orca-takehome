"""In-process pub/sub - the cross-app integration contract.

A publisher (e.g. cases/router.py) never imports or knows about its
subscribers (e.g. command_view/service.py). It only publishes an Event.
Any app can subscribe to any event type at startup. This is deliberately
"a simple in-process event emitter" per the brief - the contract (Event
classes + subscribe/publish) is what would carry over to a real queue
later without changing any app's code.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Event:
    pass


@dataclass(frozen=True)
class CaseClosed(Event):
    case_id: str
    country: str


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)


EVENT_BUS = EventBus()
