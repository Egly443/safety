#!/usr/bin/env python3
"""Run one task in its own process group with sampled resource guards."""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--seconds', type=int, default=1200)
p.add_argument('--rss-gib', type=float, default=4)
p.add_argument('--cwd', required=True)
p.add_argument('--record', required=True)
p.add_argument('--log', required=True)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ['--'] else a.command
if not command:
    p.error('a command is required')
root = Path(__file__).resolve().parents[1]
record = {'command': command, 'cwd': a.cwd,
          'status': 'starting',
          'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'wall_limit_seconds': a.seconds, 'rss_limit_bytes': int(a.rss_gib * 1024**3),
          'rss_guard': 'sampled aggregate process-group RSS, one-second interval'}
initial_free = os.statvfs(root).f_bavail * os.statvfs(root).f_frsize
minimum_free = max(10 * 1024**3, initial_free - 8 * 1024**3)
record['minimum_free_bytes'] = minimum_free
start = time.monotonic()
peak = 0
reason = None
Path(a.record).write_text(json.dumps(record, indent=2) + '\n')

def group_rss(group):
    total = 0
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            stat = (proc / 'stat').read_text()
            fields = stat[stat.rfind(')') + 2:].split()
            if int(fields[2]) == group:
                total += int(fields[21]) * os.sysconf('SC_PAGE_SIZE')
        except (OSError, ValueError, IndexError):
            continue
    return total

with open(a.log, 'w') as log:
    child = subprocess.Popen(command, cwd=a.cwd, stdout=log, stderr=subprocess.STDOUT,
                             start_new_session=True)
    record['status'] = 'running'
    last_update = start - 10
    try:
        while child.poll() is None:
            rss = group_rss(child.pid)
            peak = max(peak, rss)
            free = os.statvfs(root).f_bavail * os.statvfs(root).f_frsize
            if time.monotonic() - last_update >= 10:
                record.update(elapsed_seconds=round(time.monotonic() - start, 3),
                              peak_sampled_rss_bytes=peak)
                Path(a.record).write_text(json.dumps(record, indent=2) + '\n')
                last_update = time.monotonic()
            if time.monotonic() - start >= a.seconds:
                reason = 'wall_limit'
            elif rss > record['rss_limit_bytes']:
                reason = 'rss_limit'
            elif free < minimum_free:
                reason = 'storage_limit'
            if reason:
                break
            time.sleep(1)
    finally:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        record.update(exit_code=child.returncode, stop_reason=reason,
                      status='stopped' if reason else 'finished',
                      elapsed_seconds=round(time.monotonic() - start, 3),
                      peak_sampled_rss_bytes=peak)
        Path(a.record).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
raise SystemExit(124 if reason else child.returncode)
