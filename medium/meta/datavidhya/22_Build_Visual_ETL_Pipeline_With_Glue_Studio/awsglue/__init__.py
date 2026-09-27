"""Local ``awsglue`` shim for offline Glue Studio runs.

The Glue Studio-generated script imports from ``awsglue``. In production
the real package is bundled on the Glue worker; offline we shadow the
small surface area the script actually uses:

    - ``awsglue.context``      -> ``GlueContext`` (create_dynamic_frame,
                                  write_dynamic_frame, create_data_frame)
    - ``awsglue.transforms``   -> ``Filter``, ``ApplyMapping``
    - ``awsglue.job``          -> ``Job`` (init/commit no-op)

The same PySpark script works in both environments because the import
path is identical.
"""
from .context import GlueContext
from .dynamic_frame import DynamicFrame
from .job import Job

__all__ = ["GlueContext", "DynamicFrame", "Job"]
