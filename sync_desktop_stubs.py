#!/usr/bin/env python3
"""
Backfill script: creates Desktop sidebar stubs for all existing CLI sessions.
Run once manually: python3 ~/.claude/sync_desktop_stubs.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from create_desktop_stub import (
    find_desktop_sessions_dir,
    get_known_cli_session_ids,
    extract_metadata,
    create_stub,
)

PROJECTS_DIR = Path.home() / ".claude" / "projects"


def main():
    sessions_dir = find_desktop_sessions_dir()
    if not sessions_dir:
        print("Error: Claude Code Desktop sessions directory not found.", file=sys.stderr)
        print("Make sure Claude Code Desktop has been launched at least once.", file=sys.stderr)
        sys.exit(1)

    known = get_known_cli_session_ids(sessions_dir)
    print(f"Found {len(known)} existing Desktop stubs.")

    if not PROJECTS_DIR.exists():
        print(f"Error: {PROJECTS_DIR} does not exist.", file=sys.stderr)
        sys.exit(1)

    jsonl_files = sorted(PROJECTS_DIR.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    print(f"Found {len(jsonl_files)} CLI session(s) in {PROJECTS_DIR}")

    created = 0
    skipped = 0
    for jsonl in jsonl_files:
        session_id = jsonl.stem
        if session_id in known:
            skipped += 1
            continue
        metadata = extract_metadata(jsonl)
        stub_path = create_stub(metadata, sessions_dir)
        print(f"  Created: {stub_path.name}  [{metadata['cwd']}]  {metadata['title']!r}")
        created += 1

    print(f"\nDone. {created} stub(s) created, {skipped} already existed.")
    if created > 0:
        print("Relaunch Claude Code Desktop to see the new sessions in the sidebar.")


if __name__ == "__main__":
    main()
