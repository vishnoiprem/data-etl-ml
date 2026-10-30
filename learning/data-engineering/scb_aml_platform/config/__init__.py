"""Configuration package.

Exposes the settings module so `from scb_aml_platform import config`
gives access to `config.settings` (the test suite monkeypatches
attributes on that submodule). Individual settings are imported from
`scb_aml_platform.config.settings` directly rather than re-exported
here — a star import would hide every name from static analysis
(ruff F403) and make it impossible to tell where a constant comes
from.
"""

from . import settings

__all__ = ["settings"]
