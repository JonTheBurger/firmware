# ruff: noqa: TC003 - Typer needs to be able to see all definitions at runtime.
import io
import json
import sys
from pathlib import Path
from typing import Annotated, cast

from typer import Context, Option, Typer

import project.core.backtrace
import project.core.runtime
from project.cli.args import ProjectPathArgument
from project.commands.fix import fix
from project.commands.fmt import fmt
from project.commands.lint import lint
from project.core.config import BaseConfig
from project.core.error.user import UserError
from project.core.logger import Log
from project.core.units import byte
from project.system.files import FileType

query_app = Typer(
    name="query",
    help="Lookup information about the project",
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    suggest_commands=True,
    pretty_exceptions_enable=False,
)


@query_app.command(name="files")
def cli_query_files(
    ctx: Context,
    *,
    files: Annotated[list[Path], ProjectPathArgument],
    as_json: Annotated[bool, Option("--json", help="Enable JSON output")] = False,
) -> None:
    """Lookup project files."""

    out = cast("io.TextIOWrapper", sys.stdout)
    if as_json:
        delimiter = "  "
        out.write("[")
        for file in files:
            out.write(delimiter)
            out.write(
                json.dumps(
                    {
                        "path": str(file),
                        "file_type": str(FileType.detect(file) or FileType.ALL),
                    }
                ),
            )
            delimiter = ",\n  "
        out.write("\n]\n")
    else:
        for file in files:
            out.write(f"{file}\n")


app = Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    suggest_commands=True,
    pretty_exceptions_enable=True,
)
app.add_typer(query_app)


@app.command(name="fmt", help=fmt.__doc__)
def cli_fmt(ctx: Context, files: Annotated[list[Path], ProjectPathArgument]) -> None:
    fmt(files)


@app.command(name="fix", help=fix.__doc__)
def cli_fix(ctx: Context, files: Annotated[list[Path], ProjectPathArgument]) -> None:
    fix(files)


@app.command(name="lint", help=lint.__doc__)
def cli_lint(ctx: Context, files: Annotated[list[Path], ProjectPathArgument]) -> None:
    lint(files)


def help_for(field: str) -> str:
    description = BaseConfig.model_fields[field].description
    if not description:
        raise ValueError("Missing common CLI field description!")
    return description


@app.callback()
def cli(
    ctx: Context,
    *,
    verbose: Annotated[int, Option("--verbose", "-v", count=True, envvar="VERBOSE", help=help_for("verbose"))] = 0,
    config: Annotated[
        Path | None, Option("--config", "-c", exists=True, dir_okay=False, help=help_for("config"))
    ] = None,
    jobs: Annotated[int, Option("--jobs", "-j", help=help_for("jobs"))] = 0,
) -> None:
    """Project Development Tool Suite."""
    # Typer hackily overrides the global handler even when disabled, so we re-install our handler after typer.
    project.core.backtrace.setup()
    ctx.obj = BaseConfig.model_validate(locals(), strict=True)
    del verbose, config, jobs


def main() -> None:
    with project.core.runtime.setup():
        log = Log.get(__name__)
        with log.span("cli") as span:
            try:
                span.warning("nice")
                span.metric.binary_size("application.elf", 100 * byte)
                app()
            except UserError as error:
                print(error)


if __name__ == "__main__":
    main()
