"""The formats that are specific to this application."""

from dataclasses import dataclass, field
from enum import StrEnum
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Self, TextIO

from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic import BaseModel
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

from project.core.dirs import html_dir, project_dir
from project.format.sarif import Sarif, SarifLevel
from project.util.file_range import FileRange
from project.util.json import JsonEncoder
from project.util.maybe import maybe

if TYPE_CHECKING:
    from collections.abc import Iterable

    from _typeshed import StrPath


class Severity(StrEnum):
    NONE = ""
    NOTE = "note"
    WARNING = "warning"
    ERROR = "error"

    @classmethod
    def from_sarif(cls, level: SarifLevel) -> Self:
        match level:
            case SarifLevel.ERROR:
                return cls.ERROR
            case SarifLevel.WARNING:
                return cls.WARNING
            case SarifLevel.NOTE:
                return cls.NOTE
            case _:
                return cls.NONE


class Diagnostic(BaseModel):
    extent: FileRange
    message: str
    tool: str = ""
    rule: str = ""
    language: str = "text"
    severity: Severity = Severity.NONE

    def __str__(self) -> str:
        """In ``<file>:<line>:<column>: <severity>: <message> [<rule>]`` format."""
        string = f"{self.extent}: "
        if self.severity != Severity.NONE:
            string += f"{self.severity}: "
        string += self.message
        if self.rule:
            string += f"[{self.rule}]"
        return string

    def source_code(self, *, context_lines: int = 0) -> str:
        expanded = self.extent.expand_lines(context_lines)
        lines = list(expanded.read_lines())
        underline = self.extent.underline()
        row = expanded.start.line - self.extent.start.line
        row = self.extent.start.line - expanded.start.line + 1
        lines.insert(row, underline)
        return "\n".join(lines)

    @classmethod
    def from_sarif(cls, sarif: Sarif) -> Iterable[Diagnostic]:
        for run in sarif.runs:
            for result in run.results:
                maybe_location = maybe(result.locations[0].physical_location)
                file: Path = (
                    maybe_location.and_then(lambda x: x.artifact_location)
                    .and_then(lambda x: x.uri)
                    .and_then(Path.from_uri)
                    .or_else(project_dir)
                )
                tool: str = maybe(run.tool).and_then(lambda tool: tool.driver).and_then(lambda d: d.name).or_else(str)
                maybe_region = maybe_location.and_then(lambda x: x.region)
                extent = FileRange(file, 1, 5)
                if region := maybe_region.option:
                    extent = FileRange(
                        file,
                        ((region.start_line or 1), (region.start_column or 1)),
                        ((region.end_line or 1), (region.end_column or 1) - 1),
                    )
                yield Diagnostic(
                    extent=extent,
                    message=result.message.markdown or result.message.text or "<unknown>",
                    tool=tool,
                    severity=Severity.from_sarif(result.level),
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
        env.policies["json.dumps_kwargs"] = {"cls": JsonEncoder}
        template = env.get_template("report.html.j2")

        rows = []
        for index, diagnostic in enumerate(self.diagnostics):
            row = diagnostic.model_dump()
            row["file"] = diagnostic.extent.file.relative_to(project_dir())
            row["rule"] = row["rule"] or f"diagnostic-{index}"
            # Pygments escapes the source text and emits only its own span markup.
            row["highlighted_source"] = _highlight_source(diagnostic)
            rows.append(row)

        status_counts = {status: sum(d.severity == status for d in self.diagnostics) for status in Severity}

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


def _highlight_source(diagnostic: Diagnostic) -> str:
    """Return Pygments HTML. Unknown lexer names safely fall back to plain text."""
    if diagnostic.severity == Severity.NOTE:
        return ""

    try:
        lexer = get_lexer_by_name(diagnostic.language)
    except ClassNotFound:
        lexer = TextLexer()

    return highlight(
        diagnostic.source_code(context_lines=3),
        lexer,
        HtmlFormatter(nowrap=False, linenos="table", linenostart=diagnostic.extent.start.line, cssclass="source-code"),
    )
