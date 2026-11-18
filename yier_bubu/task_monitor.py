"""Read Codex lifecycle events locally, without retaining messages or tool data."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import time

EVENTS = {"task_started", "task_complete", "turn_aborted"}
MARKERS = tuple(value.encode("ascii") for value in EVENTS)


@dataclass(frozen=True)
class Event:
    kind: str
    stamp: float
    turn_id: str


def decode(record):
    if b'"event_msg"' not in record or not any(mark in record for mark in MARKERS):
        return None
    try:
        item = json.loads(record)
        detail = item.get("payload") or {}
        kind = detail.get("type")
        if item.get("type") == "event_msg" and kind in EVENTS:
            stamp = datetime.fromisoformat(item["timestamp"]).timestamp()
            return Event(kind, stamp, detail.get("turn_id") or "")
    except (ValueError, UnicodeError, TypeError, KeyError, AttributeError):
        return None
    return None


def last_event(path):
    """Search backward from EOF. Ignore a partially written last JSON record."""
    with path.open("rb") as stream:
        position = stream.seek(0, 2)
        pending = b""
        first = True
        while position > 0:
            size = min(position, 256 * 1024)
            position -= size
            stream.seek(position)
            lines = (stream.read(size) + pending).split(b"\n")
            pending = lines[0] if position else b""
            complete = lines[1:] if position else lines
            if first:
                complete = complete[:-1]
                first = False
            for line in reversed(complete):
                event = decode(line)
                if event is not None:
                    return event
        return None


class TaskMonitor:
    def __init__(self, sessions):
        self.sessions = Path(sessions)
        self.cache = {}
        self.known = {}
        self.initialized = False
        self.success_deadline = 0.0
        self.last_scan = 0.0
        self.recent_paths = set()

    def sample(self, *, engine_started, now=None):
        now = time.time() if now is None else now
        if engine_started is None:
            self.known.clear()
            self.recent_paths.clear()
            self.last_scan = 0
            self.success_deadline = 0
            self.initialized = False
            return "idle", 0

        if not self.last_scan or now - self.last_scan >= 3:
            self.recent_paths = set(self.sessions.rglob("rollout-*.jsonl"))
            self.last_scan = now
        current = {}
        for path in self.recent_paths:
            try:
                stat = path.stat()
                if stat.st_mtime + 2 < engine_started:
                    continue
                signature = stat.st_size, stat.st_mtime_ns
                cached = self.cache.get(path)
                if cached is None or signature != cached[0]:
                    # An active last event remains valid even if other items are appended.
                    event = last_event(path)
                    self.cache[path] = signature, event
                event = self.cache[path][1]
                if event and event.stamp >= engine_started - 2:
                    current[path] = event
            except OSError:
                if path in self.known:
                    current[path] = self.known[path]

        active = sum(event.kind == "task_started" for event in current.values())
        new_success = any(event.kind == "task_complete" and
                          self.known.get(path) != event and
                          (self.known.get(path) is not None or now - event.stamp < 8)
                          for path, event in current.items())
        if active:
            self.success_deadline = 0
        elif self.initialized and new_success:
            self.success_deadline = now + 4
        self.known = current
        self.initialized = True
        return ("running", active) if active else ("review" if now < self.success_deadline else "idle", 0)
