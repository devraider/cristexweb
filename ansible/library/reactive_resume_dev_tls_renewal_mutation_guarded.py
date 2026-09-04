#!/usr/bin/python3
"""Lint-only module resolution shim for the paired TLS mutation action.

Ansible action-plugin lookup has precedence over a same-named module.  The
shim makes that registration explicit to ansible-lint while ensuring that an
unexpected module dispatch can only fail closed and never mutate the host.
"""

from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule


def main() -> None:
    module = AnsibleModule(argument_spec={}, supports_check_mode=True)
    module.fail_json(msg="the guarded TLS mutation action plugin was not dispatched")


if __name__ == "__main__":
    main()
