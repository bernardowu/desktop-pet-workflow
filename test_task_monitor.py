from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from yier_bubu.platform_support import elapsed_seconds
from yier_bubu.task_monitor import TaskMonitor


class TaskMonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sessions = Path(self.temp.name)
        self.monitor = TaskMonitor(self.sessions)
        self.now = time.time()

    def record(self, stem, kind, offset, *, partial=False):
        line = json.dumps({
            "type":"event_msg",
            "timestamp":datetime.fromtimestamp(self.now+offset,timezone.utc).isoformat(),
            "payload":{"type":kind,"turn_id":stem},
        }).encode("utf-8")
        with (self.sessions/f"rollout-{stem}.jsonl").open("ab") as fh:
            fh.write(line if partial else line+b"\n")

    def sample(self, offset):
        return self.monitor.sample(engine_started=self.now-10,now=self.now+offset)

    def test_loop_has_no_idle_timeout_while_task_is_active(self):
        self.record("long","task_started",0)
        self.assertEqual(self.sample(1),("running",1))
        self.assertEqual(self.sample(3600),("running",1))

    def test_parallel_turns_wait_for_the_last_completion(self):
        self.record("a","task_started",0)
        self.record("b","task_started",0)
        self.assertEqual(self.sample(1),("running",2))
        self.record("a","task_complete",1)
        self.assertEqual(self.sample(2),("running",1))
        self.record("b","task_complete",2)
        self.assertEqual(self.sample(3),("review",0))
        self.assertEqual(self.sample(8),("idle",0))

    def test_incomplete_write_does_not_end_task(self):
        self.record("recent","task_started",0)
        self.assertEqual(self.sample(1),("running",1))
        self.record("recent","task_complete",1,partial=True)
        self.assertEqual(self.sample(2),("running",1))
        with (self.sessions/"rollout-recent.jsonl").open("ab") as fh:
            fh.write(b"\n")
        self.assertEqual(self.sample(3),("review",0))

    def test_abort_and_engine_shutdown_return_to_idle(self):
        self.record("a","task_started",0)
        self.assertEqual(self.sample(1),("running",1))
        self.record("a","turn_aborted",1)
        self.assertEqual(self.sample(2),("idle",0))
        self.assertEqual(self.monitor.sample(engine_started=None,now=self.now+3),("idle",0))

    def test_macos_process_elapsed_formats(self):
        self.assertEqual(elapsed_seconds("03:42"),222)
        self.assertEqual(elapsed_seconds("02:03:42"),7422)
        self.assertEqual(elapsed_seconds("1-02:03:42"),93822)
