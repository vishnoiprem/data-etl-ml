"""Top-level conftest for the section 5 code tree.

Adds every immediate subdirectory of ``05_managing_ec2/code/`` to
``sys.path`` so that the per-subdir test scripts can
``import <sibling_module>`` without computing relative paths.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _name in os.listdir(_HERE):
    _subdir = os.path.join(_HERE, _name)
    if os.path.isdir(_subdir) and not _name.startswith("__"):
        sys.path.insert(0, _subdir)
