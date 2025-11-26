"""最小化实现的 offline_requests 模块，用于本地 FastAPI 测试。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from pydantic import ValidationError
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException

from api import ecommerce_api


@dataclass
class Response:
    """简单的响应对象，兼容 tests 中的调用方式。"""

    status_code: int
    _data: Any

    def __post_init__(self):
        self.text = json.dumps(self._data, ensure_ascii=False) if self._data is not None else ""

    def json(self) -> Any:
        return self._data

    def raise_for_status(self):
        if 400 <= self.status_code:
            detail = self._data.get("detail") if isinstance(self._data, dict) else self.text
            raise HTTPException(status_code=self.status_code, detail=detail)
        return self


class Session:
    """极简 Session，实现 get/post/put/delete 方法。"""

    def __init__(self):
        self.headers: Dict[str, str] = {}

    def update_headers(self, headers: Dict[str, str]):
        self.headers.update(headers)

    def close(self):
        pass

    # 请求方法
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> Response:  # noqa: ARG002
        return self._request("GET", url, params=params, headers=headers)

    def post(self, url: str, json: Optional[Dict[str, Any]] = None, timeout: int = 10,
             headers: Optional[Dict[str, str]] = None, **kwargs) -> Response:  # noqa: ARG002
        return self._request("POST", url, json=json, headers=headers)

    def put(self, url: str, json: Optional[Dict[str, Any]] = None, timeout: int = 10,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> Response:  # noqa: ARG002
        return self._request("PUT", url, json=json, headers=headers)

    def delete(self, url: str, timeout: int = 10, headers: Optional[Dict[str, str]] = None,
               **kwargs) -> Response:  # noqa: ARG002
        return self._request("DELETE", url, headers=headers)

    # 内部调度
    def _request(
            self,
            method: str,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if params:
            for key, value in params.items():
                query_params[key] = [value]

        normalized_params = {key: values[-1] for key, values in query_params.items()}

        if parsed_url.path == "/test-dashboard":
            dashboard_path = Path(__file__).parent.parent / "assets" / "test_dashboard.html"

            if dashboard_path.exists():
                return Response(200, dashboard_path.read_text(encoding="utf-8"))
            return Response(404, {"detail": "未知路径"})

        if parsed_url.path.startswith("/api/auth/token"):
            try:
                request = ecommerce_api.LoginRequest(**(json or {}))
                token_response = ecommerce_api.login(request)
                return Response(200, token_response.model_dump())
            except HTTPException as exc:
                return Response(exc.status_code, {"detail": exc.detail})

        token = None
        if headers and "Authorization" in headers:
            token = headers["Authorization"].replace("Bearer ", "")
        elif "Authorization" in self.headers:
            token = self.headers["Authorization"].replace("Bearer ", "")
        try:
            current_user = ecommerce_api.get_current_user(token)
            status_code, data = self._dispatch(method, parsed_url.path, normalized_params, json, current_user)
        except HTTPException as exc:  # FastAPI 抛出的业务异常
            return Response(exc.status_code, {"detail": exc.detail})
        except ValidationError as exc:
            return Response(422, {"detail": exc.errors()})
        return Response(status_code, data)

    def _dispatch(
            self,
            method: str,
            path: str,
            params: Dict[str, Any],
            json_data: Optional[Dict[str, Any]],
            current_user: dict,
    ) -> Tuple[int, Any]:
        segments = [segment for segment in path.split('/') if segment]
        if not segments or segments[0] != "api":
            raise HTTPException(status_code=404, detail="未知路径")

        resource = segments[1]

        if resource == "products":
            return self._handle_products(method, segments[2:], params, json_data, current_user)
        if resource == "cart":
            return self._handle_cart(method, segments[2:], json_data, current_user)
        if resource == "promotions":
            return self._handle_promotions(method, segments[2:], current_user)
        if resource == "orders":
            return self._handle_orders(method, segments[2:], json_data, current_user)
        if resource == "auth" and len(segments) > 2 and segments[1] == "token":
            requests = ecommerce_api.LoginRequest(**(json or {}))
            token_response = ecommerce_api.login(requests)
            return 200, token_response.model_dump()

        raise HTTPException(status_code=404, detail="未知资源")

    # 资源处理方法
    def _handle_products(
            self,
            method: str,
            segments: list[str],
            params: Dict[str, Any],
            json_data: Optional[Dict[str, Any]],
            current_user: dict,
    ) -> Tuple[int, Any]:
        if method == "GET" and not segments:
            category = params.get("category")
            return 200, ecommerce_api.get_products(category=category, current_user=current_user)
        if method == "GET" and segments:
            product_id = int(segments[0])
            return 200, ecommerce_api.get_product(product_id, current_user=current_user)
        if method == "POST":
            product = ecommerce_api.ProductCreate(**(json_data or {}))
            return 201, ecommerce_api.create_product(product, current_user=current_user)
        if method == "PUT" and segments:
            product_id = int(segments[0])
            product = ecommerce_api.ProductCreate(**(json_data or {}))
            return 200, ecommerce_api.update_product(product_id, product, current_user=current_user)
        if method == "DELETE" and segments:
            product_id = int(segments[0])
            return 200, ecommerce_api.delete_product(product_id)
        raise HTTPException(status_code=405, detail="不支持的请求")

    def _handle_cart(self, method: str, segments: list[str], json_data: Optional[Dict[str, Any]], current_user: dict) -> \
    Tuple[int, Any]:
        if not segments:
            raise HTTPException(status_code=404, detail="缺少用户 ID")

        user_id = int(segments[0])
        if method == "GET" and len(segments) == 1:
            return 200, ecommerce_api.get_cart(user_id, current_user=current_user)

        if len(segments) >= 2 and segments[1] == "items":
            if method == "POST":
                item = ecommerce_api.CartItemAdd(**(json_data or {}))
                return 200, ecommerce_api.add_to_cart(user_id, item, current_user=current_user)
            if method == "DELETE" and len(segments) == 3:
                product_id = int(segments[2])
                return 200, ecommerce_api.remove_from_cart(user_id, product_id, current_user=current_user)

        raise HTTPException(status_code=405, detail="不支持的购物车操作")

    def _handle_promotions(self, method: str, segments: list[str], current_user: dict) -> Tuple[int, Any]:
        if method == "GET" and not segments:
            return 200, ecommerce_api.get_promotions(current_user=current_user)
        if method == "GET" and segments:
            promotion_id = int(segments[0])
            return 200, ecommerce_api.get_promotion(promotion_id, current_user=current_user)
        raise HTTPException(status_code=405, detail="不支持的促销操作")

    def _handle_orders(
            self,
            method: str,
            segments: list[str],
            json_data: Optional[Dict[str, Any]],
            current_user: dict,
    ) -> Tuple[int, Any]:
        if method == "POST" and not segments:
            order = ecommerce_api.OrderCreate(**(json_data or {}))
            return 201, ecommerce_api.create_order(order, current_user=current_user)
        if method == "GET" and segments:
            order_id = int(segments[0])
            return 200, ecommerce_api.get_order(order_id, current_user=current_user)
        raise HTTPException(status_code=405, detail="不支持的订单操作")


__all__ = ["Session", "Response"]
