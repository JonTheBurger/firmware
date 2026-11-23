from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field


class BaseConfig(BaseModel):
    verbose: int = Field(default=0, description="Increase the verbosity")
    config: Annotated[Path | None, Field(description="Path to config file")] = None
    jobs: int = Field(default=0, description="Number of CPUs to use; 0 for all, -N for all but N")


class SpaceConfgi(BaseModel):
    slobs: int = Field(default=0, description="Number of CPUs to use; 0 for all, -N for all but N")


class GraceConfig(BaseConfig, SpaceConfgi):
    pass
