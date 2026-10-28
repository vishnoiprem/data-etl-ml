import importlib.util
import platform
import sys

print("=" * 60)
print("PYTHON ENVIRONMENT")
print("=" * 60)
print(f"executable : {sys.executable}")
print(f"version    : {platform.python_version()}")
print(f"platform   : {platform.system()} {platform.machine()}")

# The one optional dependency the course leans on.
HAS_JINJA = importlib.util.find_spec("jinja2") is not None
print(f"jinja2     : {'installed' if HAS_JINJA else 'MISSING -> pip install jinja2'}")

# The dependency the course deliberately does NOT need.
HAS_AIRFLOW = importlib.util.find_spec("airflow") is not None
print(f"airflow    : {'installed' if HAS_AIRFLOW else 'not installed (not required)'}")

# Optional extras.
for name in ("pandas", "matplotlib", "pytest", "nbformat"):
    found = importlib.util.find_spec(name) is not None
    print(f"{name:<11}: {'installed' if found else 'not installed'}")

if HAS_JINJA:
    import jinja2
    print(f"jinja2 version: {jinja2.__version__}")
