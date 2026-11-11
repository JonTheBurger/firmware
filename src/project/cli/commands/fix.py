from typing import Annotated

from typer import Context, Typer

from project.cli.common import Common, ProjectPathArgument

app = Typer()


@app.command()
def fix(ctx: Context, files: Annotated[list[str], ProjectPathArgument]) -> None:
    common: Common = ctx.obj

    print(files)
