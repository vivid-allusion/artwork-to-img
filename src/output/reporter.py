"""Report generation for costs and status."""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from ..output.writer import OutputWriter


class Reporter:
    """Generate markdown reports for runs."""

    def __init__(self, output_writer: OutputWriter):
        """
        Initialize reporter.

        Args:
            output_writer: OutputWriter instance
        """
        self.output_writer = output_writer
        self.start_time = datetime.now()

    def _timestamp_footer(self, label: str = "Generated") -> str:
        """Generate consistent timestamp footer for reports."""
        return f"*{label} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

    def save_reports(
        self,
        success: bool,
        summary: Dict[str, Any],
        error_message: Optional[str] = None,
    ) -> None:
        """
        Save all reports based on run outcome.

        Args:
            success: Whether run was successful
            summary: Processing summary with metrics
            error_message: Error message if failed
        """
        if success:
            self._save_success_reports(summary)
        else:
            self._save_failure_report(summary, error_message)

    def _save_success_reports(self, summary: Dict[str, Any]) -> None:
        """Save success and cost reports."""
        success_report = self._generate_success_report(summary)
        self.output_writer.write_report(success_report, "SUCCESS.md")

        if summary.get("total_cost", 0) > 0:
            cost_report = self._generate_cost_report(summary)
            self.output_writer.write_report(cost_report, "COST-REPORT.md")

        logger.info("Reports saved successfully")

    def _save_failure_report(
        self,
        summary: Dict[str, Any],
        error_message: Optional[str],
    ) -> None:
        """Save failure report."""
        failure_report = self._generate_failure_report(summary, error_message)
        self.output_writer.write_report(failure_report, "FAILURE.md")

        if summary.get("processed", 0) > 0 and summary.get("total_cost", 0) > 0:
            cost_report = self._generate_cost_report(summary)
            self.output_writer.write_report(cost_report, "PARTIAL-COST-REPORT.md")

        logger.error("Failure report saved")

    def _generate_success_report(self, summary: Dict[str, Any]) -> str:
        """Generate success report content."""
        processing_time = (datetime.now() - self.start_time).total_seconds()

        report_lines = [
            "# SUCCESS",
            "",
            "## Run Summary",
            f"- **Status**: ✅ Completed Successfully",
            f"- **Total Images Generated**: {summary.get('processed', 0)}",
            f"- **Total Files Processed**: {summary.get('total_prompts', 0)}",
            f"- **Profile**: {summary.get('profile_name', 'N/A')}",
            f"- **Processing Time**: {processing_time:.2f} seconds",
            "",
        ]

        if summary.get("processed", 0) > 0:
            avg_time = processing_time / summary["processed"]
            report_lines.extend([
                "## Performance Metrics",
                f"- **Average Time per Image**: {avg_time:.2f} seconds",
                f"- **Success Rate**: 100.0%",
                "",
            ])

        report_lines.extend([
            self._timestamp_footer("Completed"),
            "",
        ])

        return "\n".join(report_lines)

    def _generate_cost_report(self, summary: Dict[str, Any]) -> str:
        """Generate cost report content."""
        total_cost = summary.get("total_cost", 0)
        processed = summary.get("processed", 0)

        report_lines = [
            "# Cost Report",
            "",
            "## Summary",
            f"- **Total Images Generated**: {processed}",
            f"- **Total Cost**: ${total_cost:.4f}",
        ]

        if processed > 0:
            avg_cost = total_cost / processed
            report_lines.append(f"- **Average Cost per Image**: ${avg_cost:.4f}")

        report_lines.extend([
            "",
            self._timestamp_footer(),
            "",
        ])

        return "\n".join(report_lines)

    def _generate_failure_report(
        self,
        summary: Dict[str, Any],
        error_message: Optional[str],
    ) -> str:
        """Generate failure report content."""
        processing_time = (datetime.now() - self.start_time).total_seconds()

        report_lines = [
            "# FAILURE",
            "",
            "## Run Summary",
            f"- **Status**: ❌ Failed",
            f"- **Images Generated Before Failure**: {summary.get('processed', 0)}",
            f"- **Failed Operations**: {summary.get('failed', 0)}",
            f"- **Processing Time**: {processing_time:.2f} seconds",
            "",
        ]

        if error_message:
            report_lines.extend([
                "## Error Details",
                f"```",
                f"{error_message}",
                f"```",
                "",
            ])

        if summary.get("processed", 0) > 0:
            report_lines.extend([
                "## Partial Results",
                f"- **Successfully Generated**: {summary['processed']} images",
                f"- **Partial Cost**: ${summary.get('total_cost', 0):.4f}",
                "",
            ])

        report_lines.extend([
            self._timestamp_footer("Failed"),
            "",
        ])

        return "\n".join(report_lines)
