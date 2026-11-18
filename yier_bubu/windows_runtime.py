"""Small Windows helpers for the read-only local task monitor."""
import ctypes as c
from ctypes import wintypes as w

kernel = c.WinDLL("kernel32", use_last_error=True)


class ProcessEntry(c.Structure):
    _fields_ = [
        ("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
        ("th32DefaultHeapID", c.c_size_t), ("th32ModuleID", w.DWORD),
        ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD),
        ("pcPriClassBase", w.LONG), ("dwFlags", w.DWORD), ("szExeFile", w.WCHAR * 260),
    ]


def api(name, result, *arguments):
    function = getattr(kernel, name)
    function.argtypes = arguments
    function.restype = result
    return function


snapshot = api("CreateToolhelp32Snapshot", w.HANDLE, w.DWORD, w.DWORD)
first = api("Process32FirstW", w.BOOL, w.HANDLE, c.POINTER(ProcessEntry))
next_process = api("Process32NextW", w.BOOL, w.HANDLE, c.POINTER(ProcessEntry))
open_process = api("OpenProcess", w.HANDLE, w.DWORD, w.BOOL, w.DWORD)
close_handle = api("CloseHandle", w.BOOL, w.HANDLE)
process_times = api("GetProcessTimes", w.BOOL, w.HANDLE, *([c.POINTER(w.FILETIME)] * 4))
create_mutex = api("CreateMutexW", w.HANDLE, w.LPVOID, w.BOOL, w.LPCWSTR)


def engine_started():
    handle = snapshot(2, 0)
    if handle in (None, c.c_void_p(-1).value):
        return None
    times = []
    entry = ProcessEntry()
    entry.dwSize = c.sizeof(entry)
    try:
        ok = first(handle, c.byref(entry))
        while ok:
            if entry.szExeFile.lower() in {"codex.exe", "codex-app-server.exe"}:
                process = open_process(0x1000, False, entry.th32ProcessID)
                if process:
                    try:
                        timestamps = [w.FILETIME() for _ in range(4)]
                        if process_times(process, *(c.byref(t) for t in timestamps)):
                            birth = timestamps[0]
                            ticks = (birth.dwHighDateTime << 32) | birth.dwLowDateTime
                            times.append(ticks / 10_000_000 - 11_644_473_600)
                    finally:
                        close_handle(process)
            ok = next_process(handle, c.byref(entry))
    finally:
        close_handle(handle)
    return min(times, default=None)


def one_instance():
    mutex = create_mutex(None, False, r"Local\YierBubuCodexPet")
    if c.get_last_error() == 183:
        close_handle(mutex)
        return None
    if not mutex:
        raise c.WinError(c.get_last_error())
    return mutex
