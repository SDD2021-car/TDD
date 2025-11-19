"""用于离线测试的 FastAPI 极简实现。"""

from typing import Any, Callable


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any):  # noqa: ARG002
        pass

    def _simple_decorator(self, func: Callable[[Callable[..., Any]], Callable[..., Any]]):
        return func

    def get(self, *args: Any, **kwargs: Any):  # noqa: ARG002
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def post(self, *args: Any, **kwargs: Any):  # noqa: ARG002
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def put(self, *args: Any, **kwargs: Any):  # noqa: ARG002
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def delete(self, *args: Any, **kwargs: Any):  # noqa: ARG002
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


__all__ = ["FastAPI", "HTTPException"]