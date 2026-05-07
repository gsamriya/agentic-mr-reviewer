from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .orchestrator import MRReviewer

app = typer.Typer(help="Agentic GitLab MR Reviewer")
console = Console()


@app.command()
def review(
    project: str = typer.Argument(..., help="GitLab project path, e.g. group/project"),
    mr_id: int = typer.Argument(..., help="Merge Request IID"),
    output_json: Optional[str] = typer.Option(
        None, "--output-json", help="Write raw JSON report to this file"
    ),
):
    """
    Run an agentic review for the given MR and print a human-readable report.
    """
    reviewer = MRReviewer()
    console.print(f"[bold]Reviewing MR !{mr_id} in {project}[/bold]")

    report = reviewer.review_merge_request(project, mr_id)

    # Pretty output
    console.print(Panel.fit(f"[bold]{report.mr.title}[/bold]\n{report.mr.web_url}"))

    console.print("\n[bold cyan]Summary[/bold cyan]")
    console.print(report.summary)

    console.print("\n[bold cyan]Risks[/bold cyan]")
    if report.risks:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Level")
        table.add_column("Reason")
        for r in report.risks:
            table.add_row(r.level, r.reason)
        console.print(table)
    else:
        console.print("No significant risks identified by the assistant.")

    console.print("\n[bold cyan]Lint issues[/bold cyan]")
    if report.lint_result.issues:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Code")
        table.add_column("Message")
        for iss in report.lint_result.issues:
            table.add_row(iss.file, str(iss.line), iss.code, iss.message)
        console.print(table)
    else:
        console.print("No lint issues (ruff).")

    console.print("\n[bold cyan]Tests[/bold cyan]")
    for case in report.test_result.cases:
        status = "[green]passed[/green]" if case.status == "passed" else "[red]failed[/red]"
        console.print(f"- {case.name}: {status}")
        if case.message and case.status == "failed":
            console.print(
                Syntax(case.message[:1000], "text", theme="ansi_dark", line_numbers=False)
            )

    console.print("\n[bold cyan]Suggested questions for the author[/bold cyan]")
    if report.suggested_questions:
        for q in report.suggested_questions:
            console.print(f"- {q}")
    else:
        console.print("No questions suggested.")

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        console.print(f"\n[green]JSON report written to {output_json}[/green]")


if __name__ == "__main__":
    app()
