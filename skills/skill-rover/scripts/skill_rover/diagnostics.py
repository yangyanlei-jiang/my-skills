"""Read-only local configuration checks; never execute configured commands."""
import json
import sys
from pathlib import Path

from . import __version__
from .catalog import regular_file
from .integration import EVENTS, _handler, _is_generated_handler, _reject_symlink_components
from .lifecycle import _now, due_records
from .store import Store


def diagnose(project, host, state_dir, router_root):
    if host not in ("codex", "claude"):
        raise ValueError("host must be codex or claude")
    project, router_root = Path(project).resolve(), Path(router_root).resolve()
    state_dir = Path(state_dir).expanduser().absolute()
    folder = ".codex" if host == "codex" else ".claude"
    config_path = project / folder / ("hooks.json" if host == "codex" else "settings.json")
    skill_path = project / (".agents" if host == "codex" else ".claude") / "skills" / "skill-rover"
    checks, observations = [], {}

    def add(code, status, message):
        checks.append({"code": code, "status": status, "message": message})

    try:
        installed = skill_path.resolve() == router_root and (skill_path / "SKILL.md").is_file()
        add("router", "pass" if installed else "error",
            "Project router points to this checkout." if installed else
            "Project router is missing or points elsewhere; inspect it before running integrate.")
        _reject_symlink_components(project, config_path)
        _reject_symlink_components(project, skill_path.parent)
        with regular_file(config_path) as stream:
            content = stream.read(2 * 1024 * 1024 + 1)
        if len(content) > 2 * 1024 * 1024:
            raise ValueError("host configuration exceeds the 2 MiB diagnostic limit")
        config = json.loads(content)
        if not isinstance(config, dict) or not isinstance(config.get("hooks"), dict):
            raise ValueError("hooks must be an object")
        if config.get("disableAllHooks") is True:
            raise ValueError("project settings disable all hooks")
        argv = [sys.executable, "-B", str(router_root / "scripts" / "rover.py"),
                "--state-dir", str(state_dir), "hook"]
        bad = []
        for event in EVENTS:
            groups = config["hooks"].get(event, [])
            if not isinstance(groups, list):
                raise ValueError("hook event must be a list")
            expected = _handler(argv, host, event)
            handlers = [handler
                        for group in groups if isinstance(group, dict) and not group.get("matcher")
                        for handler in (group.get("hooks") if isinstance(group.get("hooks"), list) else [])]
            generated = [handler for handler in handlers
                         if _is_generated_handler(handler, host, event, router_root / "scripts" / "rover.py")]
            if generated != [expected]:
                bad.append(event)
        if bad:
            raise ValueError("missing, duplicated or outdated hooks for " + ", ".join(bad)
                             + "; re-run integrate with this Python and the intended state directory")
        add("hooks", "pass", "All four project events target this interpreter, checkout and state directory.")
    except (OSError, ValueError, RuntimeError) as exc:
        add("hooks", "error", str(exc))
    add("host-trust", "warning", "Host trust, effective user/managed settings and native event delivery "
        "are not verified here. Review hooks in the host; other config layers may add or disable hooks.")

    store = Store(state_dir)
    try:
        if store.root.is_symlink() or store.path.is_symlink():
            raise ValueError("state root and state file must not be symlinks")
        # Writers replace complete snapshots atomically. Do not create a lock,
        # empty state, notices, or run archival cleanup merely to diagnose it.
        state = store._read()
        sessions = list(state.get("routing", {}).values())
        live = [item for item in sessions if item.get("ended_at") is None]
        pending = sum(item.get("decision") == "pending" for item in live)
        due = due_records(state, _now(None))
        active = [entry for entry in state["entries"].values() if entry["status"] != "retired"]
        observations = {"routing_checks": sum(item["checks"] for item in sessions),
                        "pending_routes": pending, "due_reviews": len(due),
                        "managed_active": len(active),
                        "in_use": len({identity for ids in state["uses"].values() for identity in ids})}
        add("state", "pass", "State snapshot is readable." if store.path.exists() else "No state snapshot yet.")
        if not sessions:
            add("routing-unobserved", "warning", "No routing observations; verify a new host prompt reaches the hook.")
        elif pending:
            add("routing-pending", "warning", "Routing is pending in " + str(pending)
                + " session(s); check whether the host completed use or record-route.")
        if due:
            add("review-due", "warning", str(len(due)) + " managed skill(s) await an actual comparison; "
                "a reminder or this diagnostic does not complete it.")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        add("state", "error", "State could not be interpreted; preserved for recovery: " + str(exc))
    return {"version": __version__, "project": str(project), "host": host,
            "state_dir": str(state_dir), "checks": checks, "observations": observations,
            "ok": not any(row["status"] == "error" for row in checks),
            "automatic_routing_verified": False}
