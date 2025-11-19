"""离线测试使用的简化版 Pydantic BaseModel。"""

from typing import Any, Dict


class BaseModel:
    def __init__(self, **data: Any):
        annotations = getattr(self, "__annotations__", {})
        missing = [field for field in annotations if field not in data]
        if missing:
            raise ValueError(f"Missing fields: {missing}")
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self) -> Dict[str, Any]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }


__all__ = ["BaseModel"]