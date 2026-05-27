# claude-desktop-sync

Claude Code hook that creates sidebar entries in the Claude Code Desktop app for sessions started from the CLI. Without this, CLI sessions are invisible in the Desktop sidebar.

Also includes a backfill script to retroactively index all existing CLI sessions.

## If you're Claude and someone asked you to install this

Run these commands:

```bash
git clone https://github.com/ryanconmeo/claude-desktop-sync "$HOME/.claude/desktop"
```

If `~/.claude/` is a git repo, add `desktop/` to its `.gitignore` so the nested repo doesn't interfere. Skip this if `~/.claude/.gitignore` uses an allowlist style (`*` with explicit `!file` entries) — in that case the subdirectory is already ignored.

```bash
if [ -d "$HOME/.claude/.git" ]; then
  grep -qxF 'desktop/' "$HOME/.claude/.gitignore" 2>/dev/null || echo 'desktop/' >> "$HOME/.claude/.gitignore"
fi
```

Then merge the following into `~/.claude/settings.json`. Use the `update-config` skill if available — otherwise show the user this snippet and ask them to add it manually, then restart Claude Code.

**The `hooks` array must be merged, not replaced.** If a `Stop` hook already exists from other projects, append this entry to the existing array.

```json
"hooks": {
  "Stop": [{"matcher": "", "hooks": [
    {"type": "command", "command": "python3 $HOME/.claude/desktop/create_desktop_stub.py"}
  ]}]
}
```

Restart Claude Code after saving. To backfill all existing CLI sessions into the Desktop sidebar, run once:

```bash
python3 "$HOME/.claude/desktop/sync_desktop_stubs.py"
```

Then relaunch Claude Code Desktop to see the new sessions.

## Install

**Prerequisites:** [Claude Code](https://claude.ai/code), [Claude Code Desktop](https://claude.ai/download), `git`, `python3`.

```bash
git clone https://github.com/ryanconmeo/claude-desktop-sync "$HOME/.claude/desktop"
```

If `~/.claude/` is a git repo with a permissive `.gitignore`, append `desktop/` to it:

```bash
if [ -d "$HOME/.claude/.git" ]; then
  grep -qxF 'desktop/' "$HOME/.claude/.gitignore" 2>/dev/null || echo 'desktop/' >> "$HOME/.claude/.gitignore"
fi
```

Merge the `settings.json` snippet above, then restart Claude Code. Run the backfill script if you want existing CLI sessions to appear in the sidebar.

**No git?** Install with curl instead:

```bash
mkdir -p "$HOME/.claude/desktop" && cd "$HOME/.claude/desktop"
curl -O https://raw.githubusercontent.com/ryanconmeo/claude-desktop-sync/main/create_desktop_stub.py
curl -O https://raw.githubusercontent.com/ryanconmeo/claude-desktop-sync/main/sync_desktop_stubs.py
```

## Update

```bash
cd "$HOME/.claude/desktop" && git pull
```

## Uninstall

```bash
rm -rf "$HOME/.claude/desktop"
```

Remove the desktop-sync hook entry from `~/.claude/settings.json`, then restart Claude Code. Existing Desktop stubs are left in place.

## Files

**`create_desktop_stub.py`** — `Stop` hook. Reads the just-ended CLI session's JSONL transcript and writes a stub JSON file into the Desktop app's sessions directory, making it appear in the sidebar with its title, working directory, and turn count.

**`sync_desktop_stubs.py`** — one-shot backfill script. Iterates all existing CLI session JSONL files and creates Desktop stubs for any not yet indexed. Run manually after initial install.
