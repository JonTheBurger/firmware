from pathlib import Path
from typing import Annotated

from typer import Argument, Context, Option, Typer

from project.cli.common import Common, ProjectPathArgument, complete_project_paths
from project.tools.git import Git


def fix(ctx: Context, files: Annotated[list[str], ProjectPathArgument]) -> None:
    common: Common = ctx.obj

    print(files)
