from collections.abc import Iterable  # noqa: TC003 - Typer needs to be able to see this type
from pathlib import Path

from pydantic import BaseModel, Field
from typer import Argument, Context

from project.system.files import AllFileTypes, FileType, resolve_files


class Common(BaseModel):
    verbose: int = Field(default=0, description="Increase the verbosity")
    config: Path | None = Field(default=None, description="Path to config file")
    jobs: int = Field(default=0, description="Number of CPUs to use; 0 for all, -N for all but N")


def complete_project_paths(_: Context, incomplete: str) -> list[str]:
    suggestions: list[str] = [AllFileTypes.name, FileType.CXX.name, FileType.CMAKE.name]

    current_dir = Path()
    try:
        for path in current_dir.iterdir():
            # If the user typed "src/m", filter files/folders starting with "m"
            if path.name.startswith(incomplete):
                # Append a trailing slash if it's a directory to make shell navigation seamless
                if path.is_dir():
                    suggestions.append(f"{path.name}/")
                else:
                    suggestions.append(path.name)
    except OSError:
        pass

    # Filter down the final list based on what the user typed so far
    return [s for s in suggestions if s.startswith(incomplete)]


def _resolve_files(paths: list[Path]) -> Iterable[Path]:
    """Typer needs this bridge function to see the type definitions."""
    return resolve_files(paths)


ProjectPathArgument = Argument(
    default_factory=list, allow_dash=True, autocompletion=complete_project_paths, callback=_resolve_files
)
