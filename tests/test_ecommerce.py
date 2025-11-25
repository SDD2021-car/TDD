# """
# [浏览器、测试工程师]
# |
# [ECommercceAPI 测试客户端]
# | HTTP
# [FastAPI 电商后端 Mock服务]
# |
# [内存数据库] products_db/carts_db
#
# 启动前提： FastAPI 电商服务已经在 localhost:8000上跑着
# 用ECommerceAPI封装好HTTP请求
# 用pytest写了很多测试用例去测试
# """
# # pytest -q
# import pytest
# import sys
# import os
# from typing import Callable
import sys
import pytest
import os

# 添加项目路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.http_client import ECommerceAPI
from models.dataclass_models import Product, CartItem, ShoppingCart, Promotion

# ADMIN_TOKEN = "admin-token"
# USER_TOKENS = {
#     1001: "user-1001-token",
#     1002: "user-1002-token",
#     1003: "user-1003-token",
#     2001: "user-2001-token",
# }
from api import ecommerce_api
from utils.http_client import ECommerceAPI


# @pytest.fixture(scope="session")
# def api():
#     """API 全局客户端 fixture, 默认管理员身份可访问公共资源"""
#     client = ECommerceAPI("http://localhost:8000", auth_token=ADMIN_TOKEN)
#     yield client
#     client.close()
@pytest.fixture(autouse=True)
def reset_state():
    ecommerce_api.reset_state()
    yield


# @pytest.fixture
# def user_id():
#     """测试用户 ID"""
#     return 1001
@pytest.fixture
def api_client():
    return ECommerceAPI("http://localhost:8000")


@pytest.fixture
# def user_token(user_id: int) -> str:
#     """当前默认测试用户的token"""
#     return USER_TOKENS[user_id]
def admin_client(api_client: ECommerceAPI) -> ECommerceAPI:
    api_client.authenticate("admin", "adminpass")
    return api_client


@pytest.fixture
# def token_for_user() -> Callable[[int], str]:
#     """根据用户ID获取token的便捷方法"""
#     return lambda uid: USER_TOKENS[uid]
def user_client(api_client: ECommerceAPI) -> ECommerceAPI:
    api_client.authenticate("user1001", "pass1001")
    return api_client


# ========== 商品测试 ==========
# class TestProducts:
class TestAuthentication:
    """商品功能测试"""

    def test_login_success(self, api_client: ECommerceAPI):
        token = api_client.authenticate("admin", "adminpass")
        assert token
        assert "Bearer" in api_client.client.session.headers.get("Authorization", "")

    def test_invalid_token_access(self, api_client: ECommerceAPI):
        response = api_client.client.get("/api/products", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"]

    # def test_get_products_success(self, api):
    #     """测试获取商品列表"""
    #     response = api.get_products()
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "products" in data
    #     assert len(data["products"]) > 0
    #     assert data["count"] == len(data["products"])

    # def test_get_products_by_category(self, api):
    #     """测试按分类获取商品"""
    #     response = api.get_products(category="电子产品")


class TestProduct:
    def test_get_products_requires_token(self, api_client: ECommerceAPI):
        response = api_client.client.get("/api/products")
        assert response.status_code == 401

    def test_create_product_requires_admin(self, user_client: ECommerceAPI):
        payload = {"name": "测试商品", "price": 10, "stock": 1, "category": "测试"}
        response = user_client.create_product(**payload)
        assert response.status_code == 403

    def test_create_product_validation(self, admin_client: ECommerceAPI):
        invalid_payload = {"name": "坏商品", "price": -1, "stock": 1, "category": "测试"}
        response = admin_client.create_product(**invalid_payload)
        assert response.status_code == 422

    def test_missing_required_fields(self, admin_client: ECommerceAPI):
        incomplete_payload = {"price": 100}
        response = admin_client.client.post("/api/products", json=incomplete_payload)
        assert response.status_code == 422

    def test_get_products_by_category(self, user_client: ECommerceAPI):
        response = user_client.get_products(category="电子产品")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(data["products"])
        for product in data["products"]:
            assert product["category"] == "电子产品"


#     def test_get_product_by_id(self, api):
#         """测试获取单个商品"""
#         response = api.get_product(1)
#         assert response.status_code == 200
#         product = response.json()
#         assert product["id"] == 1
#         assert "name" in product
#         assert "price" in product
#         assert product["price"] > 0
#
#     def test_get_nonexistent_product(self, api):
#         """测试获取不存在的商品"""
#         response = api.get_product(99999)
#         assert response.status_code == 404
#
#     def test_create_product(self, api):
#         """测试创建商品"""
#         response = api.create_product(
#             name="测试商品",
#             price=99.99,
#             stock=10,
#             category="测试类别"
#         )
#         assert response.status_code == 201
#         product = response.json()
#         assert product["name"] == "测试商品"
#         assert product["price"] == 99.99
#
#     def test_update_product(self, api):
#         """测试更新商品"""
#         response = api.update_product(
#             product_id=1,
#             name="更新后的商品",
#             price=6999.0,
#             stock=100,
#             category="电子产品"
#         )
#         assert response.status_code == 200
#         product = response.json()
#         assert product["name"] == "更新后的商品"
#
#     def test_dataclass_product_validation(self):
#         """测试商品数据类验证"""
#         # 正常创建
#         product = Product(
#             id=1,
#             name="测试商品",
#             price=100.0,
#             stock=10,
#             category="测试"
#         )
#         assert product.name == "测试商品"
#
#         # 负价格应抛出异常
#         with pytest.raises(ValueError):
#             Product(id=1, name="测试", price=-10, stock=10, category="测试")
#
#
# # ========== 购物车测试 ==========
# class TestShoppingCart:
#     """购物车功能测试"""
#
#     def test_add_item_to_cart(self, api, user_id, user_token):
#         """测试添加商品到购物车"""
#         response = api.add_to_cart(user_id, product_id=1, quantity=2, auth_token=user_token)
#         assert response.status_code == 200
#         cart = response.json()
#         assert cart["user_id"] == user_id
#         assert len(cart["items"]) > 0
#
#     def test_add_multiple_items(self, api, user_id, user_token):
#         """测试添加多个商品"""
#         api.add_to_cart(user_id, product_id=1, quantity=1, auth_token=user_token)
#         api.add_to_cart(user_id, product_id=2, quantity=1, auth_token=user_token)
#
#         response = api.get_cart(user_id, auth_token=user_token)
#         cart = response.json()
#         assert len(cart["items"]) >= 2
#         assert cart["total"] > 0
#
#     def test_add_out_of_stock_item(self, api, user_id, user_token):
#         """测试添加库存不足的商品"""
#         response = api.add_to_cart(user_id, product_id=1, quantity=10000, auth_token=user_token)
#         assert response.status_code == 400
#
#     def test_remove_item_from_cart(self, api, user_id, user_token):
#         """测试从购物车移除商品"""
#         api.add_to_cart(user_id, product_id=3, quantity=1, auth_token=user_token)
#         response = api.remove_from_cart(user_id, product_id=3, auth_token=user_token)
#         assert response.status_code == 200
#
#     def test_dataclass_shopping_cart(self):
#         """测试购物车数据类"""
#         cart = ShoppingCart(user_id=1)
#
#         item1 = CartItem(product_id=1, product_name="商品1", quantity=2, price=100.0)
#         item2 = CartItem(product_id=2, product_name="商品2", quantity=1, price=200.0)
#         cart.add_item(item1)
#         cart.add_item(item2)
class TestCart:
    def test_add_item_with_invalid_quantity(self, user_client: ECommerceAPI):
        payload = {"product_id": 1, "quantity": -1}
        response = user_client.client.post("/api/cart/1001/items", json=payload)
        assert response.status_code == 422
        # assert len(cart.items) == 2
        # assert cart.total == 400.0  # 2*100 + 1*200
        #
        # cart.remove_item(1)
        # assert len(cart.items) == 1
        # assert cart.total == 200.0

    def test_add_item_and_total(self, user_client: ECommerceAPI):
        payload = {"product_id": 1, "quantity": 2}
        response = user_client.add_to_cart(1001, **payload)
        assert response.status_code == 200
        cart_response = user_client.get_cart(1001)
        assert cart_response.status_code == 200
        cart_body = cart_response.json()
        assert cart_body["total"] == 2 * ecommerce_api.products_db[1]["price"]

    # # ========== 促销测试 ==========
    # class TestPromotions:
    #     """促销功能测试"""
    def test_cross_user_access_denied(self, user_client: ECommerceAPI):
        response = user_client.get_cart(2001)
        assert response.status_code == 403

    # def test_get_promotions(self, api):
    #     """测试获取促销列表"""
    #     response = api.get_promotions()
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "promotions" in data
    #     assert len(data["promotions"]) > 0
    #
    # def test_get_promotion_by_id(self, api):
    #     """测试获取促销详情"""
    #     response = api.get_promotion(1)
    #     assert response.status_code == 200
    #     promo = response.json()
    #     assert promo["id"] == 1
    #     assert "discount_type" in promo
    #
    # def test_dataclass_promotion_calculation(self):
    #     """测试促销数据类计算"""
    #     # 百分比折扣
    #     promo1 = Promotion(
    #         id=1,
    #         name="9折优惠",
    #         discount_type="percentage",
    #         discount_value=10,
    #         min_amount=100
    #     )
    #
    #     assert promo1.calculate_discount(1000) == 100  # 1000 * 10%
    #     assert promo1.calculate_discount(50) == 0  # 不满足最低金额
    #
    #     # 固定金额折扣
    #     promo2 = Promotion(
    #         id=2,
    #         name="满100减20",
    #         discount_type="fixed",
    #         discount_value=20,
    #         min_amount=100
    #     )
    #
    #     assert promo2.calculate_discount(150) == 20
    #     assert promo2.calculate_discount(80) == 0


# ========== 订单测试 ==========
class TestOrders:
    """订单功能测试"""

    # def test_create_order_without_promotion(self, api, user_id, user_token):
    #     """测试创建无促销订单"""
    #     # 先添加商品到购物车
    #     api.add_to_cart(user_id, product_id=1, quantity=1, auth_token=user_token)
    def test_create_order_with_empty_cart(self, user_client: ECommerceAPI):
        response = user_client.create_order(1001)
        assert response.status_code == 400

        # # 创建订单
        # response = api.create_order(user_id, auth_token=user_token)

    def test_create_order_flow(self, user_client: ECommerceAPI):
        user_client.add_to_cart(1001, product_id=1, quantity=1)
        response = user_client.create_order(1001)
        assert response.status_code == 201
        order = response.json()
        # assert order["user_id"] == user_id
        assert order["total"] == order["subtotal"]  # 无折扣
        assert order["status"] == "pending"

    # def test_create_order_with_promotion(self, api, token_for_user):
    #     """测试创建带促销的订单"""
    #     user_id = 1002
    #     user_token = token_for_user(user_id)
    #     # 添加商品到购物车
    #     api.add_to_cart(user_id, product_id=2, quantity=1, auth_token=user_token)  # 12999元商品
    #
    #     # 使用促销创建订单
    #     response = api.create_order(user_id, promotion_id=1, auth_token=user_token)  # 满1000减100
    def test_apply_promotion(self, user_client: ECommerceAPI):
        user_client.add_to_cart(1001, product_id=2, quantity=1)
        response = user_client.create_order(1001, promotion_id=1)
        assert response.status_code == 201
        order = response.json()
        assert order["discount"] > 0
        assert order["total"] < order["subtotal"]

    # def test_get_order(self, api, token_for_user):
    #     """测试获取订单"""
    #     user_id = 1003
    #     user_token = token_for_user(user_id)
    #     api.add_to_cart(user_id, product_id=3, quantity=1, auth_token=user_token)
    #     create_response = api.create_order(user_id, auth_token=user_token)
    #     order_id = create_response.json()["id"]
    #
    #     response = api.get_order(order_id, auth_token=user_token)


class TestDashBoard:
    def test_dashboard_served(self, admin_client: ECommerceAPI):
        response = admin_client.client.get("/test-dashboard")
        assert response.status_code == 200
        # order = response.json()
        # assert order["id"] == order_id

        # def test_create_order_empty_cart(self, api, token_for_user):
        #     """测试空购物车创建订单"""
        #     user_id = 1002
        #     user_token = token_for_user(user_id)
        #     response = api.create_order(user_id, auth_token=user_token)
        #     assert response.status_code == 400

        #
        # # ========== 集成测试 ==========
        # class TestIntegration:
        #     """端到端集成测试"""
        #
        #     def test_complete_shopping_flow(self, api, token_for_user):
        #         """测试完整购物流程"""
        #         user_id = 2001
        #         user_token = token_for_user(user_id)
        #         # 1. 浏览商品
        #         products_response = api.get_products(auth_token=user_token)
        #         assert products_response.status_code == 200
        #
        #         # 2. 添加商品到购物车
        #         api.add_to_cart(user_id, product_id=1, quantity=2, auth_token=user_token)
        #         api.add_to_cart(user_id, product_id=3, quantity=1, auth_token=user_token)
        #
        #         # 3. 查看购物车
        #         cart_response = api.get_cart(user_id, auth_token=user_token)
        #         assert cart_response.status_code == 200
        #         cart = cart_response.json()
        #         assert len(cart["items"]) == 2
        #
        #         # 4. 查看促销
        #         promotions_response = api.get_promotions(auth_token=user_token)
        #         assert promotions_response.status_code == 200
        #
        #         # 5. 创建订单
        #         order_response = api.create_order(user_id, promotion_id=2, auth_token=user_token)
        #         assert order_response.status_code == 201
        #         order = order_response.json()
        #
        #         # 6. 验证订单
        #         assert order["total"] > 0
        #         assert "created_at" in order
        #
        #         # 7. 验证购物车已清空
        #         cart_after = api.get_cart(user_id, auth_token=user_token).json()
        #         assert len(cart_after["items"]) == 0
        assert "可视化测试面板" in response.text
