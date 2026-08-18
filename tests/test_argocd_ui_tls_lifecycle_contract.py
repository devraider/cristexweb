from pathlib import Path
import stat
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / 'ansible/files/policies/argocd-ui-tls-lifecycle.yml'
RUNBOOK = ROOT / 'runbooks/argocd-ui-tls-lifecycle.md'
VALIDATOR = ROOT / 'ansible/bin/validate-argocd-ui-tls-material'

class ArgoCdUiTlsLifecycleContractTests(unittest.TestCase):
    def test_exact_browser_trusted_private_contract(self):
        p = yaml.safe_load(POLICY.read_text())
        self.assertEqual('argo.cristex-soft.com', p['hostname'])
        self.assertEqual(['argo.cristex-soft.com'], p['certificate']['exact_san_set'])
        self.assertEqual('_acme-challenge.argo.cristex-soft.com', p['certificate']['exact_challenge_name'])
        self.assertEqual(['argo.cristex-soft.com', '_acme-challenge.argo.cristex-soft.com'], p['cloudflare']['mutation_scope'])
        self.assertFalse(p['cloudflare']['proxied'])
        self.assertEqual('forbidden', p['cloudflare']['tunnel'])

    def test_infisical_and_kubernetes_contracts_are_exact(self):
        p = yaml.safe_load(POLICY.read_text())
        self.assertEqual('/argocd-ui', p['infisical']['path'])
        self.assertEqual({'ARGOCD_UI_TLS_CRT', 'ARGOCD_UI_TLS_KEY'}, set(p['infisical']['keys']))
        self.assertEqual('argocd-ui-tls', p['kubernetes']['target_secret'])
        self.assertEqual(['tls.crt', 'tls.key'], p['kubernetes']['keys'])
        self.assertTrue(p['certificate']['private_key_never_in_git_argv_logs_or_opentofu_state'])

    def test_runbook_forbids_scope_widening_and_documents_rollback(self):
        text = RUNBOOK.read_text()
        for required in ('DNS-01', '_acme-challenge.argo.cristex-soft.com', 'prod:/argocd-ui', 'creationPolicy:', 'direct `kubectl` writes', 'rollback'):
            self.assertIn(required, text)
        self.assertNotIn('*.cristex-soft.com', text)

    def test_validator_is_private_and_no_log(self):
        self.assertTrue(VALIDATOR.exists())
        # Git preserves only the executable bit, normalizing executable files to 0755.
        # Protected key inputs, not this value-free validator, remain mode 0600.
        self.assertEqual(0o755, stat.S_IMODE(VALIDATOR.stat().st_mode))
        text = VALIDATOR.read_text()
        for required in ('checkhost argo.cristex-soft.com', 'checkend 86400', 'cmp -s', 'mode 0600'):
            self.assertIn(required, text)
        self.assertNotIn('cat "$key"', text)

if __name__ == '__main__':
    unittest.main()
