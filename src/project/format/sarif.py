from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class _SarifModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Sarif(_SarifModel):
    schema_uri: Annotated[str | None, Field(alias="$schema")] = None
    version: str
    runs: Annotated[list[SarifRun], Field(default_factory=list)]


class SarifRun(_SarifModel):
    results: Annotated[list[SarifResult], Field(default_factory=list)]
    tool: SarifTool | None = None


class SarifTool(_SarifModel):
    driver: SarifToolComponent


class SarifToolComponent(_SarifModel):
    name: str
    information_uri: Annotated[str | None, Field(alias="informationUri")] = None
    version: str | None = None
    rules: Annotated[list[SarifReportingDescriptor], Field(default_factory=list)]


class SarifReportingDescriptor(_SarifModel):
    id: str
    name: str | None = None
    kind: str | None = None
    short_description: Annotated[SarifMessage | None, Field(alias="shortDescription")] = None
    full_description: Annotated[SarifMessage | None, Field(alias="fullDescription")] = None
    help: SarifMessage | None = None
    help_uri: Annotated[str | None, Field(alias="helpUri")] = None
    default_configuration: Annotated[SarifConfigurationOverride | None, Field(alias="defaultConfiguration")] = None
    properties: Annotated[dict[str, Any], Field(default_factory=dict)]


class SarifConfigurationOverride(_SarifModel):
    enabled: bool | None = None
    level: str | None = None


class SarifResult(_SarifModel):
    rule_id: Annotated[str | None, Field(alias="ruleId")] = None
    level: str | None = None
    message: SarifMessage
    locations: Annotated[list[SarifLocation], Field(default_factory=list)]
    fixes: Annotated[list[SarifFix], Field(default_factory=list)]


class SarifMessage(_SarifModel):
    text: str | None = None
    markdown: str | None = None


class SarifLocation(_SarifModel):
    physical_location: Annotated[SarifPhysicalLocation | None, Field(alias="physicalLocation")] = None


class SarifPhysicalLocation(_SarifModel):
    artifact_location: Annotated[SarifArtifactLocation | None, Field(alias="artifactLocation")] = None
    region: SarifRegion | None = None


class SarifArtifactLocation(_SarifModel):
    uri: str | None = None
    uri_base_id: Annotated[str | None, Field(alias="uriBaseId")] = None


class SarifRegion(_SarifModel):
    start_line: Annotated[int | None, Field(alias="startLine")] = None
    start_column: Annotated[int | None, Field(alias="startColumn")] = None
    end_line: Annotated[int | None, Field(alias="endLine")] = None
    end_column: Annotated[int | None, Field(alias="endColumn")] = None


class SarifFix(_SarifModel):
    description: SarifMessage | None = None
    artifact_changes: Annotated[
        list[SarifArtifactChange],
        Field(default_factory=list, alias="artifactChanges"),
    ]


class SarifArtifactChange(_SarifModel):
    artifact_location: Annotated[SarifArtifactLocation, Field(alias="artifactLocation")]
    replacements: Annotated[list[SarifReplacement], Field(default_factory=list)]


class SarifReplacement(_SarifModel):
    deleted_region: Annotated[SarifRegion, Field(alias="deletedRegion")]
    inserted_content: Annotated[SarifArtifactContent | None, Field(alias="insertedContent")] = None


class SarifArtifactContent(_SarifModel):
    text: str | None = None
