"""course_options.py — a custom PipelineOptions subclass for the course."""

from __future__ import annotations

from apache_beam.options.pipeline_options import PipelineOptions


class CourseOptions(PipelineOptions):
    """Options for the course pipelines."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--local_threshold",
            type=float,
            default=0.0,
            help="Minimum order amount in EUR to count toward revenue.",
        )
        parser.add_argument(
            "--environment_name",
            default="local",
            help="A label for the deployment environment.",
        )
        parser.add_argument(
            "--write_to_gcs",
            action="store_true",
            default=False,
            help="Whether the output path is a gs:// URI.",
        )

    @property
    def local_threshold(self) -> float:
        """The minimum order amount to count toward revenue."""
        return self._all_options["local_threshold"]

    @property
    def environment_name(self) -> str:
        """The deployment environment label."""
        return self._all_options["environment_name"]

    @property
    def write_to_gcs(self) -> bool:
        """Whether the output path is a gs:// URI."""
        return self._all_options["write_to_gcs"]

    def describe(self) -> dict[str, object]:
        """Summarise this options object for logging."""
        return {
            "environment_name": self.environment_name,
            "local_threshold": self.local_threshold,
            "write_to_gcs": self.write_to_gcs,
        }
