import json
import subprocess
import sys
from pathlib import Path
from common import Fixture

ROUTER = Path(__file__).resolve().parents[1]


class DiagnosticsTests(Fixture):
    def diagnose(self, project, state=None):
        return self.module("diagnostics").diagnose(
            project, "codex", state or project / ".skill-rover", ROUTER)

    def codes(self, result, status):
        return {row["code"] for row in result["checks"] if row["status"] == status}

    def test_missing_integration_is_actionable_and_creates_nothing(self):
        project = self.base / "not-created"
        result = self.diagnose(project)
        self.assertIn("router", self.codes(result, "error"))
        self.assertIn("hooks", self.codes(result, "error"))
        self.assertFalse(project.exists())
        self.assertFalse(result["automatic_routing_verified"])

    def test_configured_hooks_do_not_claim_host_execution(self):
        project = self.base / "project"
        state = project / ".skill-rover"
        self.module("integration").integrate(project, "codex", state, ROUTER)
        result = self.diagnose(project)
        self.assertEqual(self.codes(result, "error"), set())
        self.assertIn("host-trust", self.codes(result, "warning"))
        self.assertIn("routing-unobserved", self.codes(result, "warning"))
        self.assertFalse(state.exists())
        self.assertFalse(result["automatic_routing_verified"])

    def test_mismatched_state_or_missing_event_fails_configuration_check(self):
        project = self.base / "project"
        self.module("integration").integrate(project, "codex", self.base / "elsewhere", ROUTER)
        self.assertIn("hooks", self.codes(self.diagnose(project), "error"))
        config = project / ".codex" / "hooks.json"
        data = json.loads(config.read_text())
        data["hooks"].pop("UserPromptSubmit")
        config.write_text(json.dumps(data))
        self.assertIn("hooks", self.codes(self.diagnose(project, self.base / "elsewhere"), "error"))

    def test_pending_routing_and_due_reviews_are_reported_without_changing_state(self):
        project = self.base / "project"
        state_dir = project / ".skill-rover"
        self.module("integration").integrate(project, "codex", state_dir, ROUTER)
        store = self.module("store").Store(state_dir)
        self.module("routing").begin(store, "session", "turn", now=1)
        life = self.module("lifecycle")
        entry = life.install(store, self.skill(), review_seconds=1, now=1)
        life.load(store, entry["id"], "session", now=2)
        before = store.path.read_bytes()
        result = self.diagnose(project)
        self.assertIn("routing-pending", self.codes(result, "warning"))
        self.assertIn("review-due", self.codes(result, "warning"))
        self.assertEqual(result["observations"]["in_use"], 1)
        self.assertEqual(store.path.read_bytes(), before)

    def test_corrupt_state_is_diagnosed_without_resetting_it(self):
        project = self.base / "project"
        state = project / ".skill-rover"
        state.mkdir(parents=True)
        path = state / "state.json"
        path.write_text('{"version":')
        before = path.read_bytes()
        self.assertIn("state", self.codes(self.diagnose(project), "error"))
        self.assertEqual(path.read_bytes(), before)

    def test_large_host_configuration_is_not_limited_like_a_skill_manifest(self):
        project = self.base / "project"
        self.module("integration").integrate(project, "claude", project / ".skill-rover", ROUTER)
        config_path = project / ".claude" / "settings.json"
        config = json.loads(config_path.read_text())
        config["permissions"] = {"allow": ["Read(/workspace/" + "a" * 60 + str(i) + "/**)" for i in range(1000)]}
        config_path.write_text(json.dumps(config))
        result = self.module("diagnostics").diagnose(project, "claude", project / ".skill-rover", ROUTER)
        self.assertNotIn("hooks", self.codes(result, "error"))

    def test_stale_generated_hook_next_to_correct_hook_is_not_reported_healthy(self):
        project = self.base / "project"
        integration = self.module("integration")
        integration.integrate(project, "codex", project / ".skill-rover", ROUTER)
        config_path = project / ".codex" / "hooks.json"
        config = json.loads(config_path.read_text())
        for event in integration.EVENTS:
            old = integration._handler([str(self.base / "retired-python"), str(ROUTER / "scripts" / "rover.py"),
                                        "--state-dir", str(project / "old-state"), "hook"], "codex", event)
            config["hooks"][event].append({"hooks": [old]})
        config_path.write_text(json.dumps(config))
        self.assertIn("hooks", self.codes(self.diagnose(project), "error"))

    def test_doctor_cli_defaults_to_target_project_and_exits_nonzero_on_errors(self):
        project = self.base / "missing"
        result = subprocess.run([sys.executable, str(ROUTER / "scripts" / "rover.py"),
                                 "doctor", "--project", str(project), "--host", "codex"],
                                text=True, capture_output=True, cwd=self.base)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["state_dir"], str(project / ".skill-rover"))
        self.assertFalse(project.exists())
