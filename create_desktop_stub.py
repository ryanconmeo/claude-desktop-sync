#!/usr/bin/env python3
"""
Stop hook: creates a Claude Code Desktop sidebar stub for the just-ended CLI session.
Also importable by sync_desktop_stubs.py for backfilling.
"""
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path


SESSIONS_BASE = Path.home() / "Library" / "Application Support" / "Claude" / "claude-code-sessions"


def find_desktop_sessions_dir():
    """Return the innermost UUID directory where stub files live, or None."""
    if not SESSIONS_BASE.exists():
        return None
    for app_dir in SESSIONS_BASE.iterdir():
        if not app_dir.is_dir():
            continue
        for workspace_dir in app_dir.iterdir():
            if workspace_dir.is_dir():
                return workspace_dir
    return None


def get_known_cli_session_ids(sessions_dir):
    """Return set of cliSessionId values already indexed."""
    known = set()
    for f in sessions_dir.glob("local_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            cli_id = data.get("cliSessionId")
            if cli_id:
                known.add(cli_id)
        except Exception:
            pass
    return known


def extract_metadata(jsonl_path):
    """Parse a CLI session JSONL and return a Desktop stub dict."""
    path = Path(jsonl_path)
    session_id = path.stem

    cwd = None
    model = None
    permission_mode = "acceptEdits"
    title = None
    timestamps = []
    completed_turns = 0

    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                rec_type = rec.get("type", "")

                if not cwd and rec.get("cwd"):
                    cwd = rec["cwd"]

                ts = rec.get("timestamp")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        timestamps.append(dt.timestamp() * 1000)
                    except Exception:
                        pass

                if rec_type == "ai-title":
                    ai_title = rec.get("aiTitle", "").strip()
                    if ai_title:
                        title = ai_title[:80]

                elif rec_type == "permission-mode":
                    pm = rec.get("permissionMode", "auto")
                    permission_mode = "acceptEdits" if pm == "auto" else pm

                elif rec_type == "user":
                    completed_turns += 1
                    if title is None:
                        content = rec.get("message", {}).get("content", "")
                        if isinstance(content, str):
                            text = content.strip()
                            # skip command-injected content (slash commands, skill invocations)
                            if text and not text.startswith("<"):
                                title = text[:80]

                elif rec_type == "assistant" and model is None:
                    model = rec.get("message", {}).get("model")

    except Exception as e:
        print(f"[create_desktop_stub] Error reading {path}: {e}", file=sys.stderr)

    now_ms = int(time.time() * 1000)
    created_at = int(min(timestamps)) if timestamps else now_ms
    last_activity = int(max(timestamps)) if timestamps else now_ms

    return {
        "sessionId": f"local_{uuid.uuid4()}",
        "cliSessionId": session_id,
        "cwd": cwd or str(path.parent),
        "originCwd": cwd or str(path.parent),
        "lastFocusedAt": last_activity,
        "createdAt": created_at,
        "lastActivityAt": last_activity,
        "model": model or "claude-sonnet-4-6",
        "effort": "high",
        "isArchived": False,
        "title": title or "Untitled session",
        "titleSource": "auto",
        "permissionMode": permission_mode,
        "remoteMcpServersConfig": [],
        "completedTurns": completed_turns,
        "alwaysAllowedReasons": [],
        "sessionPermissionUpdates": [],
        "classifierSummaryEnabled": True,
    }


def create_stub(metadata, sessions_dir):
    """Write a stub JSON file. Returns the path written."""
    stub_path = sessions_dir / f"{metadata['sessionId']}.json"
    stub_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return stub_path


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = payload.get("session_id", "")
    transcript_path = payload.get("transcript_path", "")

    if not session_id or not transcript_path:
        sys.exit(0)

    sessions_dir = find_desktop_sessions_dir()
    if not sessions_dir:
        print("[create_desktop_stub] Desktop sessions directory not found", file=sys.stderr)
        sys.exit(0)

    known = get_known_cli_session_ids(sessions_dir)
    if session_id in known:
        sys.exit(0)

    metadata = extract_metadata(transcript_path)
    stub_path = create_stub(metadata, sessions_dir)
    print(f"[create_desktop_stub] Created stub: {stub_path.name} ({metadata['title']!r})", file=sys.stderr)


if __name__ == "__main__":
    main()
