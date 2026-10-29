"""Top-level conftest for the section 4 code tree.

Adds every immediate subdirectory to sys.path so that the per-subdir
test scripts can `import <sibling_module>` and `import <handler>`
without each test having to compute relative paths.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _name in os.listdir(_HERE):
    _subdir = os.path.join(_HERE, _name)
    if os.path.isdir(_subdir) and os.path.isfile(os.path.join(_subdir, "__init__.py")):
        sys.path.insert(0, _subdir)
