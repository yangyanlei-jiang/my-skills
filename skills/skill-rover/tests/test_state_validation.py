import copy
import json
import subprocess
import sys
from pathlib import Path
from common import Fixture


class StateValidationTests(Fixture):
    def test_corrupt_lifecycle_fields_fail_open_without_mutating_state(self):
        store = self.module("store").Store(self.base / "state")
        life = self.module("lifecycle")
        entry = life.install(store, self.skill(), now=0)
        life.load(store, entry["id"], "session", now=1)
        original = store.read()
        cases = [
            ("entries", {entry["id"]: None}),
            ("entries", {entry["id"]: {**original["entries"][entry["id"]], "review_seconds": "bad"}}),
            ("entries", {entry["id"]: {**original["entries"][entry["id"]], "loaded_at": True}}),
            ("entries", {entry["id"]: {**original["entries"][entry["id"]], "loaded_at": 10**400}}),
            ("uses", {"session": None}),
            ("uses", {"session": ["missing-entry"]}),
            ("notices", {"session": "bad"}),
        ]
        cli = Path(__file__).resolve().parents[1] / "scripts" / "rover.py"
        for field, value in cases:
            with self.subTest(field=field, value=value):
                state = copy.deepcopy(original)
                state[field] = value
                store.path.write_text(json.dumps(state))
                before = store.path.read_bytes()
                result = subprocess.run([sys.executable, "-B", str(cli), "--state-dir", str(store.root), "hook"],
                    input=json.dumps({"session_id": "session", "hook_event_name": "PostToolUse"}),
                    text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), {})
                self.assertIn("preserved for recovery", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(store.path.read_bytes(), before)
