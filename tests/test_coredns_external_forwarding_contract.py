from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = ROOT / "ansible/roles/coredns_external_forwarding/defaults/main.yml"
TASKS = ROOT / "ansible/roles/coredns_external_forwarding/tasks/main.yml"
PLUGIN = ROOT / "ansible/plugins/action/coredns_external_forwarding_guarded_patch.py"
WRAPPER = ROOT / "ansible/bin/configure-coredns-external-forwarding"


class CoreDnsExternalForwardingContractTests(unittest.TestCase):
    def test_exact_field_replacement_is_guarded(self):
        defaults = DEFAULTS.read_text()
        self.assertIn("forward . /etc/resolv.conf", defaults)
        self.assertIn("forward . 1.1.1.1 1.0.0.1", defaults)
        tasks = TASKS.read_text()
        self.assertIn("op: test", tasks)
        self.assertIn("op: replace", tasks)
        self.assertIn("/data/Corefile", tasks)
        self.assertNotIn("state: absent", tasks)

    def test_wrapper_and_action_are_non_passthrough(self):
        wrapper = WRAPPER.read_text()
        self.assertIn('check ] || [ "$1" = apply', wrapper)
        self.assertIn("env -i", wrapper)
        self.assertIn("--diff", wrapper)
        plugin = PLUGIN.read_text()
        self.assertIn("EXPECTED_KEYS", plugin)
        self.assertIn('args.get("namespace") == "kube-system"', plugin)
        self.assertIn('args.get("name") == "coredns"', plugin)
        self.assertIn("start_at_task", plugin)
        self.assertIn("skip_tags", plugin)


if __name__ == "__main__":
    unittest.main()
