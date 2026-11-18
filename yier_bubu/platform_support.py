"""Platform-specific process discovery and single-instance locking."""
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
import time


def app_data():
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home()/"AppData/Local"))/"YierBubuPet"
    return Path.home()/"Library/Application Support/YierBubuPet"


def elapsed_seconds(value):
    days, separator, clock = value.partition("-")
    total = int(days)*86400 if separator else 0
    parts = (clock if separator else days).split(":")
    return total + sum(int(part)*60**i for i,part in enumerate(reversed(parts)))


def engine_started():
    if sys.platform == "win32":
        from yier_bubu.windows_runtime import engine_started as windows_start
        return windows_start()
    try:
        output = subprocess.run(["/bin/ps","-ax","-o","etime=","-o","comm="],
                                capture_output=True,text=True,check=True,timeout=3).stdout
    except (OSError,subprocess.SubprocessError):
        return None
    now = time.time()
    times = []
    for line in output.splitlines():
        fields = line.split(None,1)
        if len(fields) == 2 and Path(fields[1]).name in {"codex","codex-app-server"}:
            try:
                times.append(now - elapsed_seconds(fields[0]))
            except ValueError:
                continue
    return min(times,default=None)


@contextmanager
def instance(data_dir):
    if sys.platform == "win32":
        from yier_bubu.windows_runtime import close_handle, one_instance
        mutex = one_instance()
        try:
            yield bool(mutex)
        finally:
            if mutex:
                close_handle(mutex)
        return

    import fcntl
    with (data_dir/"app.lock").open("a+") as lock:
        try:
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
        else:
            yield True
