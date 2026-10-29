#!/usr/bin/env python3
"""Fetch pinned sources and check tag identity; never overwrite existing trees."""
import json
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[1]
pins = json.loads((root / "sources.lock.json").read_text())
for name in ("codex", "bubblewrap"):
    pin = pins[name]
    dest = root / "upstream" / name
    if not dest.exists():
        subprocess.run(["git", "clone", "--depth", "1", "--branch", pin["tag"],
                        pin["url"], str(dest)], check=True)
    actual = subprocess.check_output(
        ["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    tag = subprocess.check_output(
        ["git", "-C", str(dest), "rev-parse", pin["tag"] + "^{commit}"],
        text=True).strip()
    if actual != pin["commit"] or tag != pin["commit"]:
        raise SystemExit(f"{name}: source identity mismatch; refusing to continue")
    print(f"{name}: verified {actual}")
