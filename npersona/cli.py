"""NPersona CLI — npersona generate / run / report."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


@click.group()
@click.version_option(package_name="npersona")
def main() -> None:
    """NPersona — AI security test suite generator."""


# ── npersona run ──────────────────────────────────────────────────────────────

@main.command()
@click.argument("system_doc", type=click.Path(exists=True))
@click.option("--arch", "architecture_doc", default=None, type=click.Path(exists=True),
              help="Architecture document for RCA (optional).")
@click.option("--provider", default="groq", show_default=True,
              type=click.Choice(["groq", "openai", "gemini", "azure", "ollama"]))
@click.option("--api-key", envvar="NPERSONA_API_KEY", default=None,
              help="LLM API key. Falls back to NPERSONA_API_KEY env var.")
@click.option("--model", default=None, help="LLM model override.")
@click.option("--num-adv", default=10, show_default=True, help="Number of adversarial test cases.")
@click.option("--num-user", default=10, show_default=True, help="Number of user-centric test cases.")
@click.option("--no-known-attacks", is_flag=True, default=False,
              help="Disable the research-backed known-attacks corpus augmentation.")
@click.option("--endpoint", default=None, help="Target system endpoint for automated execution.")
@click.option("--rca", is_flag=True, default=False, help="Enable RCA (requires --arch).")
@click.option("--output", "-o", default=None, type=click.Path(),
              help="Output path for the report (JSON). Defaults to stdout.")
@click.option("--format", "output_format", default="markdown",
              type=click.Choice(["json", "markdown"]), show_default=True)
@click.option("--executor-concurrency", default=4, type=int, show_default=True,
              help="Parallel test execution concurrency (1-64).")
@click.option("--executor-retries", default=3, type=int, show_default=True,
              help="Retries per test request on transient failure (0-10).")
@click.option("--executor-adapter", default="json-post",
              type=click.Choice(["json-post", "openai-chat", "bedrock-agent"]),
              show_default=True, help="Request format adapter.")
@click.option("--executor-rps", default=None, type=float,
              help="Rate limit: requests-per-second (None = unlimited).")
@click.option("--per-request-timeout", default=30.0, type=float, show_default=True,
              help="Timeout per individual request in seconds.")
@click.option("--cache-dir", default=None, type=click.Path(),
              help="Directory for profile caching. Speeds up repeated runs on same doc.")
@click.option("--verbose", "-v", is_flag=True, default=False)
def run(
    system_doc: str,
    architecture_doc: str | None,
    provider: str,
    api_key: str | None,
    model: str | None,
    num_adv: int,
    num_user: int,
    no_known_attacks: bool,
    endpoint: str | None,
    rca: bool,
    output: str | None,
    output_format: str,
    executor_concurrency: int,
    executor_retries: int,
    executor_adapter: str,
    executor_rps: float | None,
    per_request_timeout: float,
    cache_dir: str | None,
    verbose: bool,
) -> None:
    """Run the full NPersona pipeline on SYSTEM_DOC.

    Examples:\n
      npersona run spec.pdf --provider groq --api-key gsk_...\n
      npersona run spec.pdf --arch arch.pdf --rca --output report.md --format markdown\n
      npersona run spec.pdf --endpoint https://myai.com/chat --output results.json
    """
    _setup_logging(verbose)

    if rca and not architecture_doc:
        console.print("[red]--rca requires --arch to be provided.[/red]")
        sys.exit(1)

    messages: list[str] = []

    def on_progress(event: dict) -> None:
        msg = f"[{event.get('stage', '?').upper()}] {event.get('message', '')}"
        messages.append(msg)
        console.print(f"  [dim]{msg}[/dim]")

    console.print(f"\n[bold cyan]NPersona[/bold cyan] — running pipeline on [green]{system_doc}[/green]\n")

    try:
        from npersona.client import NPersonaClient
        from npersona.models.config import LLMConfig, NPersonaConfig

        llm = LLMConfig(
            provider=provider,  # type: ignore[arg-type]
            model=model or _default_model(provider),
            api_key=api_key,
        )
        config = NPersonaConfig(
            llm=llm,
            num_adversarial=num_adv,
            num_user_centric=num_user,
            enable_rca=rca,
            enable_executor=endpoint is not None,
            system_endpoint=endpoint,
            executor_concurrency=executor_concurrency,
            executor_retries=executor_retries,
            executor_adapter=executor_adapter,  # type: ignore[arg-type]
            executor_rate_limit_rps=executor_rps,
            per_request_timeout=per_request_timeout,
        )
        client = NPersonaClient(config=config, cache_dir=cache_dir)
        report = asyncio.run(
            client.run(
                system_doc=system_doc,
                architecture_doc=architecture_doc,
                include_known_attacks=not no_known_attacks,
                on_progress=on_progress,
            )
        )
    except Exception as exc:
        console.print(f"\n[red]Pipeline failed:[/red] {exc}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Output
    if output_format == "json":
        content = report.export_json()
    else:
        content = report.export_markdown()

    if output:
        Path(output).write_text(content, encoding="utf-8")
        console.print(f"\n[green]Report saved to:[/green] {output}")
    else:
        console.print("\n" + content)

    # Summary table
    _print_summary(report)

    # Exit non-zero if critical failures exist (CI/CD friendly)
    if report.critical_failures > 0:
        sys.exit(1)


# ── npersona generate (test suite only, no execution) ─────────────────────────

@main.command()
@click.argument("system_doc", type=click.Path(exists=True))
@click.option("--provider", default="groq", show_default=True)
@click.option("--api-key", envvar="NPERSONA_API_KEY", default=None)
@click.option("--model", default=None)
@click.option("--num-adv", default=10, show_default=True)
@click.option("--num-user", default=10, show_default=True)
@click.option("--output", "-o", required=True, type=click.Path(), help="Output JSON file for test suite.")
@click.option("--cache-dir", default=None, type=click.Path())
@click.option("--verbose", "-v", is_flag=True, default=False)
def generate(
    system_doc: str,
    provider: str,
    api_key: str | None,
    model: str | None,
    num_adv: int,
    num_user: int,
    output: str,
    cache_dir: str | None,
    verbose: bool,
) -> None:
    """Generate a test suite JSON without executing it.

    Example:\n
      npersona generate spec.pdf --output suite.json
    """
    _setup_logging(verbose)

    def on_progress(event: dict) -> None:
        console.print(f"  [dim][{event.get('stage', '?').upper()}] {event.get('message', '')}[/dim]")

    console.print(f"\n[bold cyan]NPersona[/bold cyan] — generating test suite for [green]{system_doc}[/green]\n")

    try:
        from npersona.client import NPersonaClient
        from npersona.models.config import LLMConfig, NPersonaConfig

        llm = LLMConfig(provider=provider, model=model or _default_model(provider), api_key=api_key)  # type: ignore[arg-type]
        config = NPersonaConfig(llm=llm, num_adversarial=num_adv, num_user_centric=num_user)
        client = NPersonaClient(config=config, cache_dir=cache_dir)

        profile = asyncio.run(client.extract_profile(system_doc, on_progress=on_progress))
        attack_map = client.map_attack_surfaces(profile, on_progress=on_progress)
        suite = asyncio.run(
            client.generate_test_suite(profile, attack_map, num_adv, num_user, on_progress=on_progress)
        )

        suite_data = suite.model_dump()
        Path(output).write_text(json.dumps(suite_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]Test suite saved:[/green] {output}")
        console.print(f"  {len(suite.adversarial_cases)} adversarial cases")
        console.print(f"  {len(suite.user_centric_cases)} user-centric cases")

    except Exception as exc:
        console.print(f"\n[red]Failed:[/red] {exc}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_summary(report) -> None:
    console.print("\n[bold]Summary[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("System", report.system_name)
    table.add_row("Tests Run", str(report.evaluation.total))
    table.add_row("Passed", f"[green]{report.evaluation.passed}[/green]")
    table.add_row("Failed", f"[red]{report.evaluation.failed}[/red]")
    table.add_row("Pass Rate", f"{report.overall_pass_rate:.1%}")
    table.add_row("Critical Failures", f"[red bold]{report.critical_failures}[/red bold]")
    table.add_row("Coverage Items", str(len(report.coverage)))
    if report.rca_findings:
        table.add_row("RCA Findings", str(len(report.rca_findings)))
    console.print(table)


def _default_model(provider: str) -> str:
    return {
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-2.0-flash",
        "azure": "gpt-4o",
        "ollama": "llama3",
    }.get(provider, "llama-3.3-70b-versatile")


if __name__ == "__main__":
    main()
