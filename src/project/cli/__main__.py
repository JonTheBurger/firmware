from pathlib import Path
from typing import Annotated

from typer import Context, Option, Typer

import project.core.runtime
from project.cli.args import ProjectPathArgument
from project.commands.fix import fix
from project.commands.fmt import fmt
from project.commands.lint import lint
from project.core.config import BaseConfig
from project.core.error.user import UserError

app = Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    suggest_commands=True,
)


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
    """"""
    ctx.obj = BaseConfig.model_validate(locals(), strict=True)
    del verbose, config, jobs


def main() -> None:
    project.core.runtime.setup()
    try:
        app()
    except UserError as error:
        print(error)


if __name__ == "__main__":
    main()
