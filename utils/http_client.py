import requests
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """封装的 HTTP 客户端"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ECommerce-Test-Client/1.0'
        })

    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求"""
        logger.info(f"{method.upper()} {url}")
        if 'json' in kwargs:
            logger.debug(f"Request Body: {kwargs['json']}")

    def _log_response(self, response: requests.Response):
        """记录响应"""
        logger.info(f"Status: {response.status_code}")
        try:
            logger.debug(f"Response: {response.json()}")
        except:
            logger.debug(f"Response: {response.text}")

    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """GET 请求"""
        url = f"{self.base_url}{endpoint}"
        self._log_request('GET', url, params=params)
        response = self.session.get(url, params=params, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response

    def post(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """POST 请求"""
        url = f"{self.base_url}{endpoint}"
        self._log_request('POST', url, json=json)
        response = self.session.post(url, json=json, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response

    def put(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """PUT 请求"""
        url = f"{self.base_url}{endpoint}"
        self._log_request('PUT', url, json=json)
        response = self.session.put(url, json=json, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE 请求"""
        url = f"{self.base_url}{endpoint}"
        self._log_request('DELETE', url)
        response = self.session.delete(url, timeout=self.timeout, **kwargs)
        self._log_response(response)
        return response

    def close(self):
        """关闭会话"""
        self.session.close()


class ECommerceAPI:
    """电商 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.client = APIClient(base_url)

    # 商品相关
    def get_products(self, category: Optional[str] = None):
        params = {"category": category} if category else None
        return self.client.get("/api/products", params=params)

    def get_product(self, product_id: int):
        return self.client.get(f"/api/products/{product_id}")

    def create_product(self, name: str, price: float, stock: int, category: str):
        data = {
            "name": name,
            "price": price,
            "stock": stock,
            "category": category
        }
        return self.client.post("/api/products", json=data)

    def update_product(self, product_id: int, name: str, price: float, stock: int, category: str):
        data = {
            "name": name,
            "price": price,
            "stock": stock,
            "category": category
        }
        return self.client.put(f"/api/products/{product_id}", json=data)

    def delete_product(self, product_id: int):
        return self.client.delete(f"/api/products/{product_id}")

    # 购物车相关
    def get_cart(self, user_id: int):
        return self.client.get(f"/api/cart/{user_id}")

    def add_to_cart(self, user_id: int, product_id: int, quantity: int):
        data = {
            "product_id": product_id,
            "quantity": quantity
        }
        return self.client.post(f"/api/cart/{user_id}/items", json=data)

    def remove_from_cart(self, user_id: int, product_id: int):
        return self.client.delete(f"/api/cart/{user_id}/items/{product_id}")

    # 促销相关
    def get_promotions(self):
        return self.client.get("/api/promotions")

    def get_promotion(self, promotion_id: int):
        return self.client.get(f"/api/promotions/{promotion_id}")

    # 订单相关
    def create_order(self, user_id: int, promotion_id: Optional[int] = None):
        data = {
            "user_id": user_id,
            "promotion_id": promotion_id
        }
        return self.client.post("/api/orders", json=data)

    def get_order(self, order_id: int):
        return self.client.get(f"/api/orders/{order_id}")

    def close(self):
        self.client.close()