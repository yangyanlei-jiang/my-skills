import base64
import json
import shlex
import subprocess
import sys
from pathlib import Path

from common import Fixture


ROUTER = Path(__file__).resolve().parents[1]


class IntegrationSafetyTests(Fixture):
    def setUp(self):
        super().setUp()
        self.integration = self.module("integration")

    def test_linked_host_directory_cannot_rewrite_external_settings(self):
        for host, folder, filename in [("claude", ".claude", "settings.json"),
                                       ("codex", ".codex", "hooks.json")]:
            with self.subTest(host=host):
                project = self.base / host
                outside = self.base / (host + "-outside")
                project.mkdir()
                outside.mkdir()
                original = '{"env": {"KEEP": "unchanged"}}\n'
                (outside / filename).write_text(original)
                (project / folder).symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    self.integration.integrate(project, host, project / ".skill-rover", ROUTER)
                self.assertEqual((outside / filename).read_text(), original)
                self.assertEqual(sorted(p.name for p in outside.iterdir()), [filename])
                self.assertEqual(sorted(p.name for p in project.iterdir()), [folder])

    def test_linked_skill_parents_are_rejected_before_config_is_written(self):
        for index, (host, relative) in enumerate([
            ("codex", ".agents"), ("codex", ".agents/skills"),
            ("claude", ".claude/skills"),
        ]):
            with self.subTest(host=host, relative=relative):
                project = self.base / ("project-" + str(index))
                outside = self.base / ("outside-" + str(index))
                project.mkdir()
                outside.mkdir()
                link = project / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    self.integration.integrate(project, host, project / ".skill-rover", ROUTER)
                self.assertEqual(list(outside.iterdir()), [])
                config = project / (".codex/hooks.json" if host == "codex" else ".claude/settings.json")
                self.assertFalse(config.exists())

    def test_dangling_parent_link_is_rejected_without_creating_external_directory(self):
        project = self.base / "project"
        project.mkdir()
        outside = self.base / "missing-outside"
        (project / ".claude").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.integration.integrate(project, "claude", project / ".skill-rover", ROUTER)
        self.assertFalse(outside.exists())
        self.assertTrue((project / ".claude").is_symlink())

    def test_explicit_symlinked_project_root_remains_supported(self):
        project = self.base / "real-project"
        project.mkdir()
        alias = self.base / "selected-project"
        alias.symlink_to(project, target_is_directory=True)
        result = self.integration.integrate(alias, "codex", project / ".skill-rover", ROUTER)
        self.assertEqual(Path(result["config"]), project.resolve() / ".codex/hooks.json")
        self.assertIn("UserPromptSubmit", json.loads(Path(result["config"]).read_text())["hooks"])
        self.assertEqual((project / ".agents/skills/skill-rover").resolve(), ROUTER.resolve())

    def test_reintegration_migrates_legacy_hooks_to_new_runtime_and_state_once(self):
        for host, relative in [("claude", ".claude/settings.json"), ("codex", ".codex/hooks.json")]:
            with self.subTest(host=host):
                project = self.base / host
                config = project / relative
                config.parent.mkdir(parents=True)
                old_state, new_state = project / "old-state", project / "new-state"
                legacy_args = ["/retired runtime/bin/python", str(ROUTER / "scripts/rover.py"),
                               "--state-dir", str(old_state), "hook"]
                hooks = {}
                unrelated = {"type": "command", "command": "echo keep"}
                for event in ("SessionStart", "UserPromptSubmit", "PostToolUse", "SessionEnd"):
                    legacy = {"type": "command", "timeout": 3 if event == "SessionEnd" else 10}
                    if host == "claude":
                        legacy.update(command=legacy_args[0], args=legacy_args[1:])
                    else:
                        legacy["command"] = shlex.join(legacy_args)
                        powershell = "& " + " ".join("'" + arg.replace("'", "''") + "'" for arg in legacy_args) + "; exit $LASTEXITCODE"
                        legacy["commandWindows"] = "powershell.exe -NoProfile -NonInteractive -EncodedCommand " + base64.b64encode(powershell.encode("utf-16-le")).decode("ascii")
                    hooks[event] = [{"hooks": [legacy, unrelated]}, {"hooks": [legacy]}]
                # A user-filtered copy is not owned by the project integration.
                filtered = {"matcher": "compact", "hooks": [dict(hooks["SessionStart"][0]["hooks"][0])]}
                hooks["SessionStart"].append(filtered)
                config.write_text(json.dumps({"env": {"KEEP": "unchanged"}, "hooks": hooks}))
                self.integration.integrate(project, host, new_state, ROUTER)
                first = config.read_text()
                self.integration.integrate(project, host, new_state, ROUTER)
                self.assertEqual(config.read_text(), first)
                saved = json.loads(first)
                self.assertEqual(saved["env"], {"KEEP": "unchanged"})
                for event, groups in saved["hooks"].items():
                    ordinary = [group for group in groups if "matcher" not in group]
                    self.assertEqual(len(ordinary), 1)
                    self.assertEqual(len(ordinary[0]["hooks"]), 2)
                    self.assertEqual(ordinary[0]["hooks"][1], unrelated)
                self.assertEqual(saved["hooks"]["SessionStart"][1], filtered)
                handler = saved["hooks"]["UserPromptSubmit"][0]["hooks"][0]
                argv = [handler["command"], *handler["args"]] if host == "claude" else shlex.split(handler["command"])
                self.assertEqual(argv[0], sys.executable)
                self.assertEqual(argv[1], "-B")
                result = subprocess.run(argv, input=json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "updated"}),
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(str(new_state), json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])
                self.assertFalse(old_state.exists())
                self.assertTrue((new_state / "state.json").is_file())

    def test_reintegration_preserves_custom_commands_and_other_router_scripts(self):
        project = self.base / "project"
        config = project / ".codex/hooks.json"
        config.parent.mkdir(parents=True)
        script = str(ROUTER / "scripts/rover.py")
        commands = [
            "echo " + shlex.quote(script),
            shlex.join([sys.executable, script, "--state-dir", str(project / "state"), "hook"]) + " && echo custom",
            shlex.join([sys.executable, str(self.base / "other-router/scripts/rover.py"), "--state-dir", str(project / "state"), "hook"]),
        ]
        groups = [{"hooks": [{"type": "command", "command": command, "timeout": 10}]} for command in commands]
        config.write_text(json.dumps({"hooks": {"UserPromptSubmit": groups}}))
        self.integration.integrate(project, "codex", project / "state", ROUTER)
        saved = json.loads(config.read_text())["hooks"]["UserPromptSubmit"]
        self.assertEqual(saved[:-1], groups)
        self.assertEqual(len(saved), 4)

    def test_unresolvable_unrelated_hook_is_preserved(self):
        project = self.base / "project"
        config = project / ".claude/settings.json"
        config.parent.mkdir(parents=True)
        loop = self.base / "unrelated.py"
        loop.symlink_to(loop)
        unrelated = {"type": "command", "timeout": 10, "command": sys.executable,
                     "args": [str(loop), "--state-dir", str(project / "state"), "hook"]}
        config.write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [unrelated]}]}}))
        self.integration.integrate(project, "claude", project / "state", ROUTER)
        saved = json.loads(config.read_text())["hooks"]["SessionStart"]
        self.assertEqual(saved[0], {"hooks": [unrelated]})
        self.assertEqual(len(saved), 2)
