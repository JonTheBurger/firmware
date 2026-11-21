from project.core.dirs import html_dir
from project.format.sarif import SarifPhysicalLocation
from collections.abc import Iterable
from project.format.sarif import Sarif
from dataclasses import asdict, dataclass, field
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TextIO

from jinja2 import Environment, PackageLoader, select_autoescape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

if TYPE_CHECKING:
    from _typeshed import StrPath

Status = Literal["error", "warning", "info"]


@dataclass(slots=True)
class Diagnostic:
    status: str | Status
    tool: str
    file: str
    message: str
    language: str = "text"
    line: int | None = None
    id: str = ""

    @classmethod
    def from_sarif(cls, sarif: Sarif) -> Iterable[Diagnostic]:
        for run in sarif.runs:
            for result in run.results:
                loc = result.locations[0].physical_location
                if loc is None:
                    continue
                loc = loc.artifact_location
                if loc is None:
                    continue
                tool = run.tool
                if tool is None:
                    continue
                tool = tool.driver
                if run.tool is None:
                    continue
                yield Diagnostic(
                    file=loc.uri or "<unknown>",
                    message=result.message.markdown or result.message.text or "<unknown>",
                    tool=tool.name or "<unknown>",
                    status=result.level,
                )


@dataclass(slots=True)
class InfoItem:
    icon: str
    heading: str
    message: str


@dataclass(slots=True)
class Report:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    info: list[InfoItem] = field(default_factory=list)
    title: str = "CI Report"
    project: str = "Project"
    revision: str = ""

    def render(self, output: TextIO | StrPath | None = None) -> None:
        env = Environment(
            loader=PackageLoader("project", "data/templates"),
            autoescape=select_autoescape(enabled_extensions=("html.j2",)),
        )
        template = env.get_template("report.html.j2")

        rows = []
        for index, diagnostic in enumerate(self.diagnostics):
            row = asdict(diagnostic)
            row["id"] = row["id"] or f"diagnostic-{index}"
            # Pygments escapes the source text and emits only its own span markup.
            row["highlighted_message"] = _highlight_message(diagnostic.message, diagnostic.language)
            rows.append(row)

        status_counts = {
            status: sum(d.status == status for d in self.diagnostics) for status in ("error", "warning", "info")
        }

        context = {
            "report": self,
            "diagnostics": rows,
            "status_counts": status_counts,
            "total": len(rows),
            "pygments_css": HtmlFormatter(style="github-dark").get_style_defs(".code-block"),
        }

        if output is None:
            output = html_dir() / "report.html"
        if isinstance(output, (str, PathLike)):
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w") as f:
                f.writelines(template.generate(**context))
        else:
            output.writelines(template.generate(**context))


def _highlight_message(message: str, language: str) -> str:
    """Return Pygments HTML. Unknown lexer names safely fall back to plain text."""
    try:
        lexer = get_lexer_by_name(language or "text")
    except ClassNotFound:
        lexer = TextLexer()

    return highlight(
        message,
        lexer,
        HtmlFormatter(nowrap=True),
    )
