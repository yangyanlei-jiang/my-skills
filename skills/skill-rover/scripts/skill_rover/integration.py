"""Project integration, per-turn routing checks and bounded review reminders."""
import base64
import json
import shlex
import sys
from pathlib import Path

from .lifecycle import _now, cleanup, due_records
from .store import atomic_json
from . import routing

EVENTS = ("SessionStart", "UserPromptSubmit", "PostToolUse", "SessionEnd")
NOTICE_SECONDS = 300
ROUTING_CONTEXT = (
    "Before acting on this request, assess its skill needs. For nontrivial multi-step work, "
    "complex logic/debugging, specialized artifacts, overlapping skills or missing capabilities, "
    "load the installed skill-rover skill and route the task even when one candidate seems obvious. "
    "Prefer installed skills; search externally only for a demonstrated gap. "
    "For reviewed, authorized selected skills, use rover.py use with --reviewed, --session and "
    "--reason to enroll and load them before applying their workflow. This starts the review clock; "
    "When a routing_check_id is supplied, pass it as --check-id to use and record-route; "
    "do not use an old check to complete a new turn. "
    "reading or natively invoking a skill alone is not tracked. Respect host invocation policies. "
    "For a simple request needing no skill, record-route --decision none with --session and "
    "--reason; do not search or enroll a skill just to fill the table. "
    "When enrollment is unavailable or unauthorized, record-route --decision blocked and report "
    "the limitation without claiming tracking started. Release managed usage at task completion. "
    "Routing checks are not completed comparisons and do not reset review deadlines. "
)

def _handler(args, host, event):
    handler = {"type": "command", "timeout": 3 if event == "SessionEnd" else 10}
    if host == "claude":
        # Exec form avoids shell-dependent quoting on all supported platforms.
        handler.update(command=args[0], args=args[1:])
    else:
        handler["command"] = shlex.join(args)
        powershell = "& " + " ".join("'" + arg.replace("'", "''") + "'" for arg in args) + "; exit $LASTEXITCODE"
        encoded = base64.b64encode(powershell.encode("utf-16-le")).decode("ascii")
        handler["commandWindows"] = "powershell.exe -NoProfile -NonInteractive -EncodedCommand " + encoded
    return handler

def _reject_symlink_components(project, path):
    # The explicitly selected project may itself be an alias; callers resolve it
    # first. Descendants must stay within that selected root before any writes.
    current = project
    for part in path.relative_to(project).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("refusing to integrate through a symlink: " + str(current))

def _is_generated_handler(handler, host, event, script):
    """Recognize only our exact command shape; leave customized hooks alone."""
    if not isinstance(handler, dict) or not isinstance(handler.get("command"), str):
        return False
    if host == "claude":
        if not isinstance(handler.get("args"), list):
            return False
        argv = [handler["command"], *handler["args"]]
    else:
        try:
            argv = shlex.split(handler["command"])
        except ValueError:
            return False
    if not all(isinstance(arg, str) for arg in argv):
        return False
    arguments = argv[1:]
    if arguments[:1] == ["-B"]:
        arguments = arguments[1:]
    if (not argv or not Path(argv[0]).is_absolute() or len(arguments) != 4
            or arguments[1] != "--state-dir" or arguments[3] != "hook"
            or not Path(arguments[0]).is_absolute() or not Path(arguments[2]).is_absolute()):
        return False
    try:
        if Path(arguments[0]).resolve() != script.resolve():
            return False
    except (OSError, RuntimeError):
        return False
    return handler == _handler(argv, host, event)

def _upsert_handler(groups, handler, host, event, script):
    result, inserted = [], False
    for group in groups:
        # Matchers or extra group fields make this a user-customized hook.
        if not isinstance(group, dict) or set(group) != {"hooks"} or not isinstance(group["hooks"], list):
            result.append(group)
            continue
        updated = []
        matched = False
        for existing in group["hooks"]:
            if _is_generated_handler(existing, host, event, script):
                matched = True
                if not inserted:
                    updated.append(handler)
                    inserted = True
            else:
                updated.append(existing)
        if updated or not matched:
            result.append({"hooks": updated})
    if not inserted:
        result.append({"hooks": [handler]})
    return result

def integrate(project, host, state_dir, router_root):
    if host not in ("codex", "claude"):
        raise ValueError("host must be codex or claude")
    project, router_root = Path(project).resolve(), Path(router_root).resolve()
    if not (router_root / "SKILL.md").is_file():
        raise ValueError("router root must contain SKILL.md")
    folder = ".codex" if host == "codex" else ".claude"
    config_path = project / folder / ("hooks.json" if host == "codex" else "settings.json")
    skill_path = project / (".agents" if host == "codex" else ".claude") / "skills" / "skill-rover"
    _reject_symlink_components(project, config_path)
    _reject_symlink_components(project, skill_path.parent)
    if skill_path.exists() or skill_path.is_symlink():
        if not skill_path.is_symlink() or skill_path.resolve() != router_root:
            raise ValueError("an unrelated skill-rover installation already exists")
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    if not isinstance(config, dict) or not isinstance(config.get("hooks", {}), dict):
        raise ValueError("existing hook configuration is not an object")
    script = router_root / "scripts" / "rover.py"
    args = [sys.executable, "-B", str(script),
            "--state-dir", str(Path(state_dir).absolute()), "hook"]
    hooks = config.setdefault("hooks", {})
    for event in EVENTS:
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise ValueError("hook event must be a list")
        handler = _handler(args, host, event)
        hooks[event] = _upsert_handler(groups, handler, host, event, script)
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        if not skill_path.is_symlink():
            skill_path.symlink_to(router_root, target_is_directory=True)
            created = True
        atomic_json(config_path, config)
    except Exception:
        if created:
            skill_path.unlink()
        raise
    return {"host": host, "skill_path": str(skill_path), "config": str(config_path),
            "state_dir": str(Path(state_dir).absolute()),
            "note": "Review/trust these hooks in your host; restart if they are not detected."}

def hook(payload, store, now=None):
    now = _now(now)
    if not isinstance(payload, dict):
        raise ValueError("hook input must be an object")
    event, session = payload.get("hook_event_name"), payload.get("session_id")
    if event not in EVENTS:
        return {}
    if not isinstance(session, str) or not session:
        raise ValueError("hook session_id is required")
    cleanup(store)
    if event == "SessionEnd":
        routing.end(store, session, now=now)
        return {}
    context = ("SkillRover session_id (literal JSON): " + json.dumps(session) + "; state directory: "
               + json.dumps(str(store.root)) + ". Use these exact values with managed load/release commands. "
               + "SkillRover helper argv (literal JSON): "
               + json.dumps([sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "rover.py"),
                             "--state-dir", str(store.root)]) + ". Append the subcommand and its arguments. ")
    current = None
    if event == "SessionStart":
        current = routing.start(store, session, now=now)
    elif event == "UserPromptSubmit":
        turn = payload.get("turn_id")
        if turn is not None and (not isinstance(turn, str) or not turn):
            raise ValueError("turn_id must be a non-empty string")
        current = routing.begin(store, session, turn, now=now)
    pending_route = event == "PostToolUse" and routing.remind_pending(store, session)
    if pending_route:
        current = store.read()["routing"][session]
    if current and current.get("check_id"):
        context += "SkillRover routing_check_id (literal JSON): " + json.dumps(current["check_id"]) + ". "
    with store.transaction() as state:
        due = due_records(state, now)
        last = state["notices"].get(session)
        remind = bool(due) and (last is None or not 0 <= now - last < NOTICE_SECONDS)
        if remind:
            state["notices"][session] = now
    # No downloaded descriptions, prompts or instructions enter developer context.
    text = context
    if event in ("SessionStart", "UserPromptSubmit"):
        text += ROUTING_CONTEXT
    elif pending_route:
        text += "SkillRover routing for this turn is still unrecorded. " + ROUTING_CONTEXT
    if remind:
        text += ("SkillRover has managed skills due for reassessment. Load the installed skill-rover "
            "skill and run its due command for this project's state directory. Compare candidates "
            "against the current task, validate any replacement, and switch only at a safe task "
            "boundary after releasing usage. A reminder is not a completed review. "
            "If review cannot complete, keep the current skill and leave the review due.")
    if text == context:
        return {}
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
