import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from interop_checker import analyze  # noqa: E402
from interop_checker.analyze import js_round  # noqa: E402


def stack(name):
    with open(os.path.join(ROOT, "examples", name + ".json")) as fh:
        return json.load(fh)


def codes(result):
    return {f["code"] for f in result["flags"]}


class ExampleStackTests(unittest.TestCase):
    """Anchors: the browser demo's author recorded these scores from a standalone Node run."""

    def test_enterprise_with_cdp_is_unified(self):
        r = analyze(stack("enterprise_with_cdp"))
        self.assertEqual(r["score"], 0)
        self.assertIn("IDENTITY_HUB", codes(r))
        # Regression: CRM and ads are linked through the CDP, so this must not be flagged.
        self.assertNotIn("CRM_ADS_DISCONNECTED", codes(r))

    def test_lean_ecommerce(self):
        r = analyze(stack("lean_ecommerce"))
        self.assertEqual(r["score"], 37)
        self.assertEqual(len(r["components"]), 2)
        self.assertIn("SPLIT_CLUSTERS", codes(r))
        self.assertIn("CRM_ADS_DISCONNECTED", codes(r))

    def test_saas_without_identity_owner(self):
        r = analyze(stack("saas_no_owner"))
        self.assertEqual(r["score"], 29)
        self.assertIn("NO_IDENTITY_OWNER", codes(r))


class RuleTests(unittest.TestCase):
    def test_fewer_than_two_tools_not_ready(self):
        self.assertFalse(analyze([])["ready"])
        self.assertFalse(analyze([{"name": "A", "category": "crm", "ids": ["phone"]}])["ready"])

    def test_isolated_tool_is_named(self):
        tools = [
            {"name": "A", "category": "crm", "ids": ["email_hash"]},
            {"name": "B", "category": "email_platform", "ids": ["email_hash"]},
            {"name": "Lonely", "category": "web_analytics", "ids": ["ip_address"]},
        ]
        r = analyze(tools)
        iso = [f for f in r["flags"] if f["code"] == "ISOLATED_TOOL"]
        self.assertEqual([f["tool"] for f in iso], ["Lonely"])

    def test_unknown_category_and_identifier_rejected(self):
        with self.assertRaises(ValueError):
            analyze([{"name": "A", "category": "nope", "ids": []}, {"name": "B", "category": "crm", "ids": []}])
        with self.assertRaises(ValueError):
            analyze([{"name": "A", "category": "crm", "ids": ["ssn"]}, {"name": "B", "category": "crm", "ids": []}])

    def test_js_round_matches_javascript_on_halves(self):
        self.assertEqual(js_round(0.5), 1)   # Python round(0.5) == 0
        self.assertEqual(js_round(2.5), 3)   # Python round(2.5) == 2
        self.assertEqual(js_round(36.666), 37)

    def test_score_always_within_bounds(self):
        ids = ["email_hash", "cookie_id", "device_id", "phone", "crm_contact_id", "ip_address"]
        cats = ["cdp", "crm", "ad_platform", "web_analytics", "email_platform", "attribution"]
        for n in range(2, 7):
            for shift in range(6):
                tools = [{"name": "T%d" % i, "category": cats[(i + shift) % 6], "ids": [ids[(i * 2 + shift) % 6]]}
                         for i in range(n)]
                self.assertTrue(0 <= analyze(tools)["score"] <= 100)


class CliTests(unittest.TestCase):
    def run_cli(self, path):
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
        return subprocess.run([sys.executable, "-m", "interop_checker", path], capture_output=True, text=True, env=env)

    def test_cli_runs_example(self):
        r = self.run_cli(os.path.join(ROOT, "examples", "lean_ecommerce.json"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("37/100", r.stdout)

    def test_cli_rejects_bad_file(self):
        bad = os.path.join(ROOT, "tests", "_bad.json")
        with open(bad, "w") as fh:
            json.dump([{"name": "A", "category": "nope", "ids": []}, {"name": "B", "category": "crm", "ids": []}], fh)
        try:
            self.assertEqual(self.run_cli(bad).returncode, 2)
        finally:
            os.remove(bad)


if __name__ == "__main__":
    unittest.main()
