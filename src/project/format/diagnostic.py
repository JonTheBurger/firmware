from pydantic import BaseModel

from project.core.logger import Log
from project.system.files import FileType
from project.util.file_range import FilePos


class Diagnostic(BaseModel):
    tool: str
    syntax: FileType | None = None
    rule: str = ""
    severity: int = Log.WARNING  #: See Log levels
    message: str
    begin: FilePos
    end: FilePos | None = None
