"""Security report model — final output of the full pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, computed_field

from npersona.models.result import EvaluationResult
from npersona.models.rca import RCAFinding

if TYPE_CHECKING:
    from npersona.models.test_suite import TestSuite


CoverageStatus = Literal["passed", "failed", "untested"]


class CoverageItem(BaseModel):
    taxonomy_id: str
    taxonomy_name: str
    team: str
    status: CoverageStatus
    test_count: int
    passed_count: int
    failed_count: int


class SecurityReport(BaseModel):
    """Complete security report for a tested AI system.

    Contains everything needed to understand what was tested and what happened —
    test suite, evaluation results, coverage, and optional RCA — in one object.
    """

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    system_name: str
    system_doc_path: str = ""
    architecture_doc_path: str = ""

    # The generated test cases — full details including trajectories and criteria
    test_suite: "TestSuite | None" = None

    evaluation: EvaluationResult
    coverage: list[CoverageItem] = Field(default_factory=list)
    rca_findings: list[RCAFinding] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def overall_pass_rate(self) -> float:
        return self.evaluation.pass_rate

    @computed_field  # type: ignore[misc]
    @property
    def critical_failures(self) -> int:
        return sum(
            1 for r in self.evaluation.failed_results if r.severity == "critical"
        )

    @computed_field  # type: ignore[misc]
    @property
    def covered_taxonomy_ids(self) -> list[str]:
        return [c.taxonomy_id for c in self.coverage if c.status == "passed"]

    @computed_field  # type: ignore[misc]
    @property
    def failed_taxonomy_ids(self) -> list[str]:
        return [c.taxonomy_id for c in self.coverage if c.status == "failed"]

    @computed_field  # type: ignore[misc]
    @property
    def untested_taxonomy_ids(self) -> list[str]:
        return [c.taxonomy_id for c in self.coverage if c.status == "untested"]

    def export_json(self, file_path: str = "security_report.json", indent: int = 2, include_test_suite: bool = True) -> str:
        """Export to JSON file.

        Args:
            file_path: Path to save JSON file.
            indent: JSON indentation level.
            include_test_suite: Set False to omit the full test suite from the output
                                (smaller file, useful when suite is stored separately).
        """
        if include_test_suite:
            json_str = self.model_dump_json(indent=indent)
        else:
            data = self.model_dump()
            data.pop("test_suite", None)
            import json
            json_str = json.dumps(data, indent=indent, default=str)

        with open(file_path, 'w') as f:
            f.write(json_str)
        return json_str

    def export_markdown(self, file_path: str = "security_report.md") -> str:
        lines: list[str] = [
            f"# NPersona Security Report — {self.system_name}",
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary",
            f"- **Pass Rate**: {self.overall_pass_rate:.1%}",
            f"- **Tests Run**: {self.evaluation.total}",
            f"- **Passed**: {self.evaluation.passed}",
            f"- **Failed**: {self.evaluation.failed}",
            f"- **Critical Failures**: {self.critical_failures}",
            "",
            "## Coverage",
            "| ID | Name | Status | Tests |",
            "|----|------|--------|-------|",
        ]
        for item in sorted(self.coverage, key=lambda c: c.taxonomy_id):
            status_emoji = {"passed": "PASS", "failed": "FAIL", "untested": "SKIP"}[item.status]
            lines.append(
                f"| {item.taxonomy_id} | {item.taxonomy_name} | {status_emoji} | {item.test_count} |"
            )

        if self.evaluation.failed_results:
            lines += ["", "## Failed Tests"]
            for result in self.evaluation.failed_results:
                lines += [
                    f"### [{result.taxonomy_id}] {result.agent_target} — {result.severity.upper()}",
                    f"**Prompt**: `{result.prompt_sent[:200]}...`",
                    f"**Response**: {result.response_received[:300]}",
                    f"**Failure**: {result.failure_reason}",
                    "",
                ]

        if self.rca_findings:
            lines += ["", "## Root Cause Analysis"]
            for finding in self.rca_findings:
                lines += [
                    f"### {finding.taxonomy_id} — {finding.agent_name}",
                    f"**Gap Type**: {finding.gap_type.replace('_', ' ').title()}",
                    f"**Spec Said**: {finding.spec_says}",
                    f"**Observed**: {finding.observed}",
                    f"**Root Cause**: {finding.root_cause}",
                    f"**Suggested Fix**: {finding.suggested_fix}",
                    f"**Fix Location**: {finding.fix_location}",
                    f"*Confidence: {finding.confidence} — {finding.confidence_note}*",
                    "",
                ]

        markdown_content = "\n".join(lines)
        with open(file_path, 'w') as f:
            f.write(markdown_content)
        return markdown_content

    def export_html(self, file_path: str = "security_report.html") -> str:
        """Export to HTML file with styling."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NPersona Security Report — {self.system_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .content {{ padding: 40px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            text-align: center;
        }}
        .summary-card h3 {{ color: #667eea; margin-bottom: 10px; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .section {{ margin: 40px 0; }}
        .section h2 {{ color: #2E86AB; border-bottom: 3px solid #A23B72; padding-bottom: 10px; margin-bottom: 20px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        table th {{
            background: #2E86AB;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        table tr:hover {{ background: #f8f9fa; }}
        .passed {{ background: #d4edda; color: #155724; }}
        .failed {{ background: #f8d7da; color: #721c24; }}
        .untested {{ background: #fff3cd; color: #856404; }}
        .test-result {{
            background: #f8f9fa;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
        }}
        .test-result h4 {{ margin-bottom: 10px; }}
        .test-result p {{ margin: 8px 0; font-size: 0.95em; }}
        .footer {{ text-align: center; padding: 20px; background: #f8f9fa; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NPersona Security Report</h1>
            <p>System: {self.system_name}</p>
            <p>Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>Summary</h2>
                <div class="summary">
                    <div class="summary-card">
                        <h3>Pass Rate</h3>
                        <div class="value">{self.overall_pass_rate:.1%}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Tests Run</h3>
                        <div class="value">{self.evaluation.total}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Passed</h3>
                        <div class="value" style="color: #28a745;">{self.evaluation.passed}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Failed</h3>
                        <div class="value" style="color: #dc3545;">{self.evaluation.failed}</div>
                    </div>
                </div>
            </div>
            <div class="section">
                <h2>Coverage Analysis</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Tests</th>
                        </tr>
                    </thead>
                    <tbody>"""

        for item in sorted(self.coverage, key=lambda c: c.taxonomy_id):
            status_class = item.status
            status_label = {"passed": "PASS", "failed": "FAIL", "untested": "SKIP"}[item.status]
            html_content += f"""
                        <tr>
                            <td>{item.taxonomy_id}</td>
                            <td>{item.taxonomy_name}</td>
                            <td><span class="{status_class}">{status_label}</span></td>
                            <td>{item.test_count}</td>
                        </tr>"""

        html_content += """
                    </tbody>
                </table>
            </div>"""

        if self.evaluation.failed_results:
            html_content += """
            <div class="section">
                <h2>Failed Tests</h2>"""
            for result in self.evaluation.failed_results:
                html_content += f"""
                <div class="test-result">
                    <h4>{result.severity.upper()} — {result.agent_target}</h4>
                    <p><strong>Prompt:</strong> {result.prompt_sent[:200]}...</p>
                    <p><strong>Response:</strong> {result.response_received[:300]}</p>
                    <p><strong>Reason:</strong> {result.failure_reason}</p>
                </div>"""
            html_content += """
            </div>"""

        html_content += """
        </div>
        <div class="footer">
            <p>Generated by NPersona v1.0.1 — AI Security Testing Framework</p>
        </div>
    </div>
</body>
</html>"""

        with open(file_path, 'w') as f:
            f.write(html_content)
        return html_content


# Rebuild model after TestSuite is available to resolve forward references
from npersona.models.test_suite import TestSuite  # noqa: E402, F401

SecurityReport.model_rebuild()
