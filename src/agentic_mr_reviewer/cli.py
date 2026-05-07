import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .orchestrator import MRReviewer

app = typer.Typer(help="Agentic GitLab MR Reviewer")
console = Console()


@app.callback(invoke_without_command=True)
def main(
    project: str = typer.Argument(None, help="GitLab project path"),
    mr_id: int = typer.Argument(None, help="Merge Request IID"),
):
    """
    Agentic GitLab MR Reviewer.

    Usage:
        mr-reviewer <PROJECT_PATH> <MR_ID>
    """

    # If user asked for help or provided no arguments, show help
    if project is None or mr_id is None:
        typer.echo(app.get_help())
        raise typer.Exit()

    reviewer = MRReviewer()
    report = reviewer.review_merge_request(project, mr_id)

    console.print(Panel.fit(f"[bold]{report.mr.title}[/bold]\n{report.mr.web_url}"))

    console.print("\n[bold cyan]Summary[/bold cyan]")
    console.print(report.summary)

    console.print("\n[bold cyan]Risks[/bold cyan]")
    if report.risks:
        table = Table(show_header=True)
        table.add_column("Level")
        table.add_column("Reason")
        for r in report.risks:
            table.add_row(r.level, r.reason)
        console.print(table)
    else:
        console.print("No significant risks identified.")

    console.print("\n[bold cyan]Suggested questions[/bold cyan]")
    if report.suggested_questions:
        for q in report.suggested_questions:
            console.print(f"- {q}")
    else:
        console.print("No questions suggested.")


if __name__ == "__main__":
    app()
