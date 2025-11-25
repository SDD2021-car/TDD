# """
# Created on 2016. 5. 28.
#     接口自动化测试必要模块
#     1、封装 GET、POST、PUT、DELETE方法
#     2、自动记录日志
#     3、管理回话
#     提供统一的HTTP客户端层，直接调用API
#
# """
# from offline_requests import Session, Response
# from typing import Optional, Dict, Any
# import logging
#
# # 记录日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# class APIClient:
#     """封装的 HTTP 客户端"""
#
#     def __init__(self, base_url: str, timeout: int = 10, auth_token: Optional[str] = None):
#         """初始化HTTP客户端，支持默认的Bear Token认证"""
#         self.base_url = base_url.rstrip('/')  # 清除尾部‘/’
#         self.timeout = timeout  # 默认端口超时时间 10s
#         self.session = Session()  # 使用会话，提高性能，支持cookie和headers复用
#         self.session.headers.update({  # 默认请求头（HTTP中自动附带在所有请求里）
#             'Content-Type': 'application/json',
#             'User-Agent': 'ECommerce-Test-Client/1.0'
#         })
#         self.auth_token = auth_token
#         if auth_token:
#             self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
#
#     def _log_request(self, method: str, url: str, **kwargs):
#         """记录请求，打印请求方法和url,若有body则打印内容"""
#         logger.info(f"{method.upper()} {url}")
#         if 'json' in kwargs:
#             logger.debug(f"Request Body: {kwargs['json']}")
#
#     def _log_response(self, response: Response):
#         """记录响应"""
#         logger.info(f"Status: {response.status_code}")
#         try:
#             logger.debug(f"Response: {response.json()}")
#         except:
#             logger.debug(f"Response: {response.text}")
#
#     def _build_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
#         """生成包含可选认证信息的请求头，支持临时覆盖默认token"""
#         headers: Dict[str, str] = {}
#         token = auth_token or self.auth_token
#         if token:  # 更新请求头
#             headers['Authorization'] = f'Bearer {token}'
#         return headers
#
#     # HTTP方法，GET、
#     def get(self, endpoint: str, params: Optional[Dict] = None, auth_token: Optional[str] = None,
#             **kwargs) -> Response:
#         """GET 请求"""
#         url = f"{self.base_url}{endpoint}"
#         self._log_request('GET', url, params=params)
#         headers = {**self._build_headers(auth_token=auth_token), **kwargs.pop('headers', {})}
#         response = self.session.get(url, params=params, timeout=self.timeout, headers=headers, **kwargs)
#         self._log_response(response)
#         return response
#
#     def post(self, endpoint: str, json: Optional[Dict] = None, auth_token: Optional[str] = None,
#              **kwargs) -> Response:
#         """POST 请求"""
#         url = f"{self.base_url}{endpoint}"
#         self._log_request('POST', url, json=json)
#         headers = {**self._build_headers(auth_token), **kwargs.pop('headers', {})}
#         response = self.session.post(url, json=json, timeout=self.timeout, headers=headers, **kwargs)
#         self._log_response(response)
#         return response
#
#     def put(self, endpoint: str, json: Optional[Dict] = None, auth_token: Optional[str] = None,
#             **kwargs) -> Response:
#         """PUT 请求"""
#         url = f"{self.base_url}{endpoint}"
#         self._log_request('PUT', url, json=json)
#         headers = {**self._build_headers(auth_token), **kwargs.pop('headers', {})}
#         response = self.session.put(url, json=json, timeout=self.timeout, headers=headers, **kwargs)
#         self._log_response(response)
#         return response
#
#     def delete(self, endpoint: str, auth_token: Optional[str] = None, **kwargs) -> Response:
#         """DELETE 请求"""
#         url = f"{self.base_url}{endpoint}"
#         self._log_request('DELETE', url)
#         headers = {**self._build_headers(auth_token), **kwargs.pop('headers', {})}
#         response = self.session.delete(url, timeout=self.timeout, headers=headers, **kwargs)
#         self._log_response(response)
#         return response
#
#     def close(self):
#         """关闭会话"""
#         self.session.close()
#
#
# class ECommerceAPI:
#     """电商 API 客户端"""
#
#     def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
#         """初始化电商API客户端，支持注入默认认证token"""
#         self.client = APIClient(base_url, auth_token=auth_token)
#
#     def authenticate(self, username: str, password: str) -> str:
#         response = self.client.post('/api/auth/token', json={'username': username, 'password': password})
#         response.raise_for_status()
#         token = response.json().get('access_token')
#         if token:
#             self.client.auth_token = token
#             self.client.session.headers.update({'Authorization': f'Bearer {token}'})
#         return token
#
#     # 商品相关
#     def get_products(self, category: Optional[str] = None, auth_token: Optional[str] = None):
#         params = {"category": category} if category else None
#         return self.client.get("/api/products", params=params, auth_token=auth_token)
#
#     def get_product(self, product_id: int, auth_token: Optional[str] = None):
#         return self.client.get(f"/api/products/{product_id}", auth_token=auth_token)
#
#     def create_product(self, name: str, price: float, stock: int, category: str, auth_token: Optional[str] = None):
#         data = {
#             "name": name,
#             "price": price,
#             "stock": stock,
#             "category": category
#         }
#         return self.client.post("/api/products", json=data, auth_token=auth_token)
#
#     def update_product(self, product_id: int, name: str, price: float, stock: int, category: str,
#                        auth_token: Optional[str] = None):
#         data = {
#             "name": name,
#             "price": price,
#             "stock": stock,
#             "category": category
#         }
#         return self.client.put(f"/api/products/{product_id}", json=data, auth_token=auth_token)
#
#     def delete_product(self, product_id: int, auth_token: Optional[str] = None):
#         return self.client.delete(f"/api/products/{product_id}", auth_token=auth_token)
#
#     # 购物车相关
#     def get_cart(self, user_id: int, auth_token: Optional[str] = None):
#         return self.client.get(f"/api/cart/{user_id}", auth_token=auth_token)
#
#     def add_to_cart(self, user_id: int, product_id: int, quantity: int, auth_token: Optional[str] = None):
#         data = {
#             "product_id": product_id,
#             "quantity": quantity
#         }
#         return self.client.post(f"/api/cart/{user_id}/items", json=data, auth_token=auth_token)
#
#     def remove_from_cart(self, user_id: int, product_id: int, auth_token: Optional[str] = None):
#         return self.client.delete(f"/api/cart/{user_id}/items/{product_id}", auth_token=auth_token)
#
#     # 促销相关
#     def get_promotions(self, auth_token: Optional[str] = None):
#         return self.client.get("/api/promotions", auth_token=auth_token)
#
#     def get_promotion(self, promotion_id: int, auth_token: Optional[str] = None):
#         return self.client.get(f"/api/promotions/{promotion_id}", auth_token=auth_token)
#
#     # 订单相关
#     def create_order(self, user_id: int, promotion_id: Optional[int] = None, auth_token: Optional[str] = None):
#         data = {
#             "user_id": user_id,
#             "promotion_id": promotion_id
#         }
#         return self.client.post("/api/orders", json=data, auth_token=auth_token)
#
#     def get_order(self, order_id: int, auth_token: Optional[str] = None):
#         return self.client.get(f"/api/orders/{order_id}", auth_token=auth_token)
#
#     def close(self):
#         self.client.close()


"""
接口自动化测试必要模块

1. 封装 GET、POST、PUT、DELETE 方法
2. 自动记录日志
3. 管理会话
4. 提供统一的 HTTP 客户端层，直接调用电商 API
"""

from typing import Optional, Dict, Any
import logging

from offline_requests import Session, Response

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """封装的 HTTP 客户端"""

    def __init__(self, base_url: str, timeout: int = 10, auth_token: Optional[str] = None):
        """
        初始化 HTTP 客户端，支持默认的 Bearer Token 认证

        :param base_url: 服务端基础地址，例如 "http://localhost:8000"
        :param timeout: 超时时间（秒）
        :param auth_token: 默认使用的认证 token，可为空
        """
        self.base_url = base_url.rstrip("/")  # 清除尾部 '/'
        self.timeout = timeout
        # 使用会话，提高性能，支持 cookie 和 headers 复用
        self.session = Session()
        # 默认请求头（会自动附加在所有请求中）
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "ECommerce-Test-Client/1.0",
            }
        )
        self.auth_token: Optional[str] = auth_token
        if auth_token:
            # 注意：这里设置的是“默认 Authorization”，后续可以被 _build_headers 覆盖
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})

    def _normalize_endpoint(self, endpoint: str) -> str:
        """确保 endpoint 以 '/' 开头，避免拼出错误 URL"""
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return endpoint

    def _log_request(self, method: str, url: str, **kwargs: Any) -> None:
        """记录请求基础信息"""
        logger.info(f"{method.upper()} {url}")
        if "params" in kwargs and kwargs["params"] is not None:
            logger.debug(f"Query Params: {kwargs['params']}")
        if "json" in kwargs and kwargs["json"] is not None:
            logger.debug(f"Request Body: {kwargs['json']}")

    def _log_response(self, response: Response) -> None:
        """记录响应"""
        logger.info(f"Status: {response.status_code}")
        try:
            logger.debug(f"Response: {response.json()}")
        except Exception:
            logger.debug(f"Response: {response.text}")

    def _build_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        """
        生成包含可选认证信息的请求头，支持临时覆盖默认 token：

        - 如果传入 auth_token，则优先使用这个 token
        - 否则使用 self.auth_token
        """
        headers: Dict[str, str] = {}
        token = auth_token or self.auth_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    # ========== HTTP 基础方法 ==========

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Response:
        """GET 请求"""
        endpoint = self._normalize_endpoint(endpoint)
        url = f"{self.base_url}{endpoint}"
        self._log_request("GET", url, params=params)
        extra_headers = kwargs.pop("headers", {})
        headers = self._build_headers(auth_token=auth_token)
        headers.update(extra_headers)

        response = self.session.get(url, params=params, timeout=self.timeout, headers=headers, **kwargs)
        self._log_response(response)
        return response

    def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Response:
        """POST 请求"""
        endpoint = self._normalize_endpoint(endpoint)
        url = f"{self.base_url}{endpoint}"
        self._log_request("POST", url, json=json)
        extra_headers = kwargs.pop("headers", {})
        headers = self._build_headers(auth_token=auth_token)
        headers.update(extra_headers)

        response = self.session.post(url, json=json, timeout=self.timeout, headers=headers, **kwargs)
        self._log_response(response)
        return response

    def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Response:
        """PUT 请求"""
        endpoint = self._normalize_endpoint(endpoint)
        url = f"{self.base_url}{endpoint}"
        self._log_request("PUT", url, json=json)
        extra_headers = kwargs.pop("headers", {})
        headers = self._build_headers(auth_token=auth_token)
        headers.update(extra_headers)

        response = self.session.put(url, json=json, timeout=self.timeout, headers=headers, **kwargs)
        self._log_response(response)
        return response

    def delete(
        self,
        endpoint: str,
        auth_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Response:
        """DELETE 请求"""
        endpoint = self._normalize_endpoint(endpoint)
        url = f"{self.base_url}{endpoint}"
        self._log_request("DELETE", url)
        extra_headers = kwargs.pop("headers", {})
        headers = self._build_headers(auth_token=auth_token)
        headers.update(extra_headers)

        response = self.session.delete(url, timeout=self.timeout, headers=headers, **kwargs)
        self._log_response(response)
        return response

    def close(self) -> None:
        """关闭会话"""
        self.session.close()


class ECommerceAPI:
    """电商业务 API 客户端（在测试中直接使用这个类）"""

    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        """
        初始化电商 API 客户端

        :param base_url: 服务基础地址
        :param auth_token: 初始 token（可选），一般在未鉴权时为空
        """
        self.client = APIClient(base_url, auth_token=auth_token)

    # ========== 鉴权相关 ==========

    def authenticate(self, username: str, password: str) -> str:
        """
        调用登录接口，获取 access_token，并自动更新到客户端的默认 Authorization 头

        成功：
            - 返回 token 字符串
            - self.client.auth_token 被更新
            - self.client.session.headers["Authorization"] 被设置（方便你的测试断言）
        失败：
            - response.raise_for_status() 抛出异常（通常是 HTTP 401）
        """
        response = self.client.post(
            "/api/auth/token",
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        if token:
            # 记录默认 token，后续所有请求都会默认带上
            self.client.auth_token = token
            # 同时更新 session.headers，方便某些测试直接检查底层 Session 的 header
            self.client.session.headers.update({"Authorization": f"Bearer {token}"})
        return token

    # ========== 商品相关 ==========

    def get_products(self, category: Optional[str] = None, auth_token: Optional[str] = None) -> Response:
        params = {"category": category} if category else None
        return self.client.get("/api/products", params=params, auth_token=auth_token)

    def get_product(self, product_id: int, auth_token: Optional[str] = None) -> Response:
        return self.client.get(f"/api/products/{product_id}", auth_token=auth_token)

    def create_product(
        self,
        name: str,
        price: float,
        stock: int,
        category: str,
        auth_token: Optional[str] = None,
    ) -> Response:
        data = {
            "name": name,
            "price": price,
            "stock": stock,
            "category": category,
        }
        return self.client.post("/api/products", json=data, auth_token=auth_token)

    def update_product(
        self,
        product_id: int,
        name: str,
        price: float,
        stock: int,
        category: str,
        auth_token: Optional[str] = None,
    ) -> Response:
        data = {
            "name": name,
            "price": price,
            "stock": stock,
            "category": category,
        }
        return self.client.put(f"/api/products/{product_id}", json=data, auth_token=auth_token)

    def delete_product(self, product_id: int, auth_token: Optional[str] = None) -> Response:
        return self.client.delete(f"/api/products/{product_id}", auth_token=auth_token)

    # ========== 购物车相关 ==========

    def get_cart(self, user_id: int, auth_token: Optional[str] = None) -> Response:
        return self.client.get(f"/api/cart/{user_id}", auth_token=auth_token)

    def add_to_cart(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
        auth_token: Optional[str] = None,
    ) -> Response:
        data = {"product_id": product_id, "quantity": quantity}
        return self.client.post(f"/api/cart/{user_id}/items", json=data, auth_token=auth_token)

    def remove_from_cart(self, user_id: int, product_id: int, auth_token: Optional[str] = None) -> Response:
        return self.client.delete(f"/api/cart/{user_id}/items/{product_id}", auth_token=auth_token)

    # ========== 促销相关 ==========

    def get_promotions(self, auth_token: Optional[str] = None) -> Response:
        return self.client.get("/api/promotions", auth_token=auth_token)

    def get_promotion(self, promotion_id: int, auth_token: Optional[str] = None) -> Response:
        return self.client.get(f"/api/promotions/{promotion_id}", auth_token=auth_token)

    # ========== 订单相关 ==========

    def create_order(
        self,
        user_id: int,
        promotion_id: Optional[int] = None,
        auth_token: Optional[str] = None,
    ) -> Response:
        data = {"user_id": user_id, "promotion_id": promotion_id}
        return self.client.post("/api/orders", json=data, auth_token=auth_token)

    def get_order(self, order_id: int, auth_token: Optional[str] = None) -> Response:
        return self.client.get(f"/api/orders/{order_id}", auth_token=auth_token)

    def close(self) -> None:
        """关闭底层 HTTP 会话"""
        self.client.close()
