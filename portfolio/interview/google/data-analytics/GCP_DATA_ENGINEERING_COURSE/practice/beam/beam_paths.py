"""Local path resolution for the Beam labs.

The course's Beam material was authored against Google Cloud Storage buckets
(``gs://bkt-2-abc1111/products.txt``).  ``gcloud`` is not available here, so
the labs run against the local copy of the same data in
``Lab-sessions-beam-dataflow/sample_data/``.

This module is the single place that knows how a cloud path maps to a local
one.  Everything else in the suite goes through :func:`local_path`.
"""

from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
COURSE = HERE.parent.parent
REPO = COURSE.parent.parent.parent

# The user's own lab material.
LAB_DIR = COURSE / "practice" / "Lab-sessions-beam-dataflow"
SAMPLE_DATA = LAB_DIR / "sample_data"
TEMPLATE_METHOD = LAB_DIR / "Template Method"
STREAMING = LAB_DIR / "Streaming Pipeline"

# The course's own generated sample data (4800 events, 12 malformed).
COURSE_SAMPLE_DATA = COURSE / "sample_data"

# Bucket name -> directory holding that bucket's files locally.
#
# The material references three buckets.  Each maps onto the shared local
# ``sample_data`` folder, because that folder holds every file the notebooks
# read, just flattened.
BUCKET_ROOTS = {
    "bkt-2-abc1111": SAMPLE_DATA,
    "src-bkt-sdk-13022025": SAMPLE_DATA,
    "dummy-bucket-gcs-test": SAMPLE_DATA,
    "test-bkt-123123123": SAMPLE_DATA,
    "source_bucket_11222023": SAMPLE_DATA,
    "source-bucket-bq": SAMPLE_DATA,
}

# Variable name -> the preamble variable that holds the local directory.
#
# The material builds bucket paths from a variable, e.g.
# ``f"gs://{BUCKET_NAME}/user_events.csv"``.  The rewrite maps that variable
# to a preamble constant that resolves to a real local directory.
VARIABLE_ROOTS = {
    "BUCKET_NAME": "_SAMPLE_ROOT",
}

# A cloud path: gs://<bucket>/<object path>
#
# Not anchored: a path can appear mid-line, as a bare string literal or as
# the argument of a transform.
GS_PATH = re.compile(r"gs://(?P<bucket>[^/\s'\"]+)/(?P<key>[^\s'\"]+)")

# An f-string cloud path: gs://{BUCKET_NAME}/<object path>
FSTRING_GS = re.compile(
    r"gs://\{(?P<bucket>[A-Za-z_][A-Za-z0-9_]*)\}/(?P<key>[^\"']+)"
)


# Where sink paths are written locally.  Read paths stay in the sample data;
# write paths are redirected here so the sample folder is never mutated.
OUT_ROOT = HERE / "_notebook_run" / "_out"

# Key prefixes that mean "this is a write target, not a source file".
SINK_KEYS = (
    "sink-folder/",
    "sink/",
    "output",
    "temp",
    "invalid/",
    "stage/",
    "staging",
)


def _is_sink(key: str) -> bool:
    return any(key.startswith(s) or s in key for s in SINK_KEYS)


def local_path(cloud_path: str) -> pathlib.Path:
    """Return the local file that stands in for a ``gs://`` path.

    >>> local_path("gs://bkt-2-abc1111/products.txt").name
    'products.txt'
    """
    match = GS_PATH.match(cloud_path)
    if not match:
        return pathlib.Path(cloud_path)

    bucket = match.group("bucket")
    key = match.group("key")
    root = BUCKET_ROOTS.get(bucket)
    if root is None:
        return pathlib.Path(cloud_path)
    if _is_sink(key):
        return OUT_ROOT / key
    return root / key


def rewrite(text: str) -> str:
    """Replace every ``gs://`` path in ``text`` with its local equivalent.

    Handles both literal paths and f-strings whose bucket name comes from a
    variable::

        TEXT_SOURCE_PATH = "gs://bkt-2-abc1111/products.txt"   -> local path
        f"gs://{BUCKET_NAME}/user_events.csv"                 -> local path

    A path whose key names a *sink* directory (``sink-folder/...``,
    ``output``, ``temp``) is redirected under the runner's output directory
    rather than into the read-only sample data.
    """
    # The f-string pass must run first: the literal pattern would otherwise
    # match ``gs://{BUCKET_NAME}/...`` and treat ``{BUCKET_NAME}`` as a bucket.
    #
    # ``match.group("bucket")`` is the *variable* name, not a bucket name, so
    # it is resolved through VARIABLE_ROOTS.  Only the ``gs://{VAR}`` prefix
    # is replaced, so the surrounding f-string stays intact.
    def fstring(match: re.Match) -> str:
        variable = match.group("bucket")
        root = VARIABLE_ROOTS.get(variable)
        if root is None:
            return match.group(0)
        key = match.group("key")
        if _is_sink(key):
            return "{_OUT_ROOT}/" + key
        return "{" + root + "}/" + key

    text = FSTRING_GS.sub(fstring, text)
    return GS_PATH.sub(lambda m: str(local_path(m.group(0))), text)


def read_rows(path: pathlib.Path, *, skip_header: bool = True) -> list[str]:
    """Return the lines of a local data file, header optionally stripped."""
    lines = path.read_text().splitlines()
    if skip_header and lines and lines[0].count(",") >= 1:
        lines = lines[1:]
    return lines
