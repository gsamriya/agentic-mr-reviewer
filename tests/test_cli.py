from typer.testing import CliRunner
import typer

from agentic_mr_reviewer.cli import main

runner = CliRunner()
app = typer.Typer()
app.command()(main)


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Root-style usage with project + MR_ID
    assert "Usage:" in result.output
    assert "PROJECT" in result.output
    assert "MR_ID" in result.output
