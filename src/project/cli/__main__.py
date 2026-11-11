from pathlib import Path
from typing import Annotated

from typer import Context, Option, Typer

import project.core.runtime
from project.cli.commands.fix import app as fix
from project.cli.commands.fmt import app as fmt
from project.cli.commands.lint import app as lint
from project.cli.common import Common
from project.core.error.user import UserError

app = Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    suggest_commands=True,
)
app.add_typer(fmt)
app.add_typer(fix)
app.add_typer(lint)


def help_for(field: str) -> str:
    description = Common.model_fields[field].description
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
    ctx.obj = Common.model_validate(locals(), strict=True)
    del verbose, config, jobs


def main() -> None:
    project.core.runtime.setup()
    try:
        app()
    except UserError as error:
        print(error)


if __name__ == "__main__":
    main()
