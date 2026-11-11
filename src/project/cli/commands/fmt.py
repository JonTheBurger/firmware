from pathlib import Path
from typing import Annotated

from typer import Context, Typer

from project.cli.common import Common, ProjectPathArgument
from project.system.files import FileType
from project.system.program import execute

app = Typer()


@app.command()
def fmt(ctx: Context, files: Annotated[list[Path], ProjectPathArgument]) -> None:
    common: Common = ctx.obj

    # --stdin-filename
    python_files = [str(f) for f in files if FileType.PY.matches(f)]
    if python_files:
        execute("ruff", ["format", "--", *python_files])
        execute("ruff", ["check", "--fix", "--fix-only", "--", *python_files])
