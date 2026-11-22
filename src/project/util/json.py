import json
from pathlib import Path

from pydantic import BaseModel


class JsonEncoder(json.JSONEncoder):
    def default(self, o: object) -> str:
        if isinstance(o, BaseModel):
            return o.model_dump_json()
        if isinstance(o, Path):
            return str(o)
        return super().default(o)
