from __future__ import annotations

from typing import Self
from xml.etree import ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field, RootModel


class JUnitModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


class Property(JUnitModel):
    name: str
    value: str | None = None


class TestMessage(JUnitModel):
    message: str | None = None
    type: str | None = None
    text: str | None = None


class TestCase(JUnitModel):
    name: str
    classname: str | None = None
    time: float | None = None
    assertions: int | None = None
    file: str | None = None
    line: int | None = None

    failure: TestMessage | None = None
    error: TestMessage | None = None
    skipped: TestMessage | None = None

    system_out: str | None = Field(default=None, alias="system-out")
    system_err: str | None = Field(default=None, alias="system-err")

    @property
    def status(self) -> str:
        if self.failure:
            return "failed"
        if self.error:
            return "error"
        if self.skipped:
            return "skipped"
        return "passed"


class TestSuite(JUnitModel):
    name: str
    tests: int | None = None
    failures: int | None = None
    errors: int | None = None
    skipped: int | None = None

    time: float | None = None
    timestamp: str | None = None
    hostname: str | None = None
    id: str | None = None
    package: str | None = None
    file: str | None = None

    properties: list[Property] = Field(default_factory=list)
    testcases: list[TestCase] = Field(default_factory=list)

    system_out: str | None = Field(default=None, alias="system-out")
    system_err: str | None = Field(default=None, alias="system-err")


class TestSuites(JUnitModel):
    tests: int | None = None
    failures: int | None = None
    errors: int | None = None
    skipped: int | None = None
    time: float | None = None

    testsuites: list[TestSuite] = Field(default_factory=list)


class JUnitReport(RootModel[TestSuite | TestSuites]):
    @classmethod
    def from_xml(cls, xml: str | bytes) -> Self:
        root = ET.fromstring(xml)
        return cls.model_validate(_parse_element(root))

    @classmethod
    def from_file(cls, path: str) -> Self:
        tree = ET.parse(path)
        return cls.model_validate(_parse_element(tree.getroot()))


def _parse_message(element: ET.Element) -> dict:
    return {
        **element.attrib,
        "text": element.text,
    }


def _parse_element(element: ET.Element) -> dict:
    """Convert a JUnit XML element into a Pydantic-compatible dictionary."""

    result = dict(element.attrib)

    for child in element:
        tag = child.tag

        if tag == "testsuite":
            result.setdefault("testsuites", []).append(_parse_element(child))

        elif tag == "testcase":
            result.setdefault("testcases", []).append(_parse_element(child))

        elif tag == "properties":
            result["properties"] = [
                {
                    **prop.attrib,
                    "value": prop.attrib.get("value", prop.text),
                }
                for prop in child
                if prop.tag == "property"
            ]

        elif tag in {"failure", "error", "skipped"}:
            result[tag] = _parse_message(child)

        elif tag in {"system-out", "system-err"}:
            result[tag] = child.text

    return result
