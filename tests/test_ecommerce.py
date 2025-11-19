import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.http_client import ECommerceAPI
from models.dataclass_models import Product, CartItem, ShoppingCart, Promotion


@pytest.fixture(scope="session")
def api():
    """API 客户端 fixture"""
    client = ECommerceAPI("http://localhost:8000")
    yield client
    client.close()


@pytest.fixture
def user_id():
    """测试用户 ID"""
    return 1001


# ========== 商品测试 ==========
class TestProducts:
    """商品功能测试"""

    def test_get_products_success(self, api):
        """测试获取商品列表"""
        response = api.get_products()
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert len(data["products"]) > 0
        assert data["count"] == len(data["products"])

    def test_get_products_by_category(self, api):
        """测试按分类获取商品"""
        response = api.get_products(category="电子产品")
        assert response.status_code == 200
        data = response.json()
        for product in data["products"]:
            assert product["category"] == "电子产品"

    def test_get_product_by_id(self, api):
        """测试获取单个商品"""
        response = api.get_product(1)
        assert response.status_code == 200
        product = response.json()
        assert product["id"] == 1
        assert "name" in product
        assert "price" in product
        assert product["price"] > 0

    def test_get_nonexistent_product(self, api):
        """测试获取不存在的商品"""
        response = api.get_product(99999)
        assert response.status_code == 404

    def test_create_product(self, api):
        """测试创建商品"""
        response = api.create_product(
            name="测试商品",
            price=99.99,
            stock=10,
            category="测试类别"
        )
        assert response.status_code == 201
        product = response.json()
        assert product["name"] == "测试商品"
        assert product["price"] == 99.99

    def test_update_product(self, api):
        """测试更新商品"""
        response = api.update_product(
            product_id=1,
            name="更新后的商品",
            price=6999.0,
            stock=100,
            category="电子产品"
        )
        assert response.status_code == 200
        product = response.json()
        assert product["name"] == "更新后的商品"

    def test_dataclass_product_validation(self):
        """测试商品数据类验证"""
        # 正常创建
        product = Product(
            id=1,
            name="测试商品",
            price=100.0,
            stock=10,
            category="测试"
        )
        assert product.name == "测试商品"

        # 负价格应抛出异常
        with pytest.raises(ValueError):
            Product(id=1, name="测试", price=-10, stock=10, category="测试")


# ========== 购物车测试 ==========
class TestShoppingCart:
    """购物车功能测试"""

    def test_add_item_to_cart(self, api, user_id):
        """测试添加商品到购物车"""
        response = api.add_to_cart(user_id, product_id=1, quantity=2)
        assert response.status_code == 200
        cart = response.json()
        assert cart["user_id"] == user_id
        assert len(cart["items"]) > 0

    def test_add_multiple_items(self, api, user_id):
        """测试添加多个商品"""
        api.add_to_cart(user_id, product_id=1, quantity=1)
        api.add_to_cart(user_id, product_id=2, quantity=1)

        response = api.get_cart(user_id)
        cart = response.json()
        assert len(cart["items"]) >= 2
        assert cart["total"] > 0

    def test_add_out_of_stock_item(self, api, user_id):
        """测试添加库存不足的商品"""
        response = api.add_to_cart(user_id, product_id=1, quantity=10000)
        assert response.status_code == 400

    def test_remove_item_from_cart(self, api, user_id):
        """测试从购物车移除商品"""
        api.add_to_cart(user_id, product_id=3, quantity=1)
        response = api.remove_from_cart(user_id, product_id=3)
        assert response.status_code == 200

    def test_dataclass_shopping_cart(self):
        """测试购物车数据类"""
        cart = ShoppingCart(user_id=1)

        item1 = CartItem(product_id=1, product_name="商品1", quantity=2, price=100.0)
        item2 = CartItem(product_id=2, product_name="商品2", quantity=1, price=200.0)

        cart.add_item(item1)
        cart.add_item(item2)

        assert len(cart.items) == 2
        assert cart.total == 400.0  # 2*100 + 1*200

        cart.remove_item(1)
        assert len(cart.items) == 1
        assert cart.total == 200.0


# ========== 促销测试 ==========
class TestPromotions:
    """促销功能测试"""

    def test_get_promotions(self, api):
        """测试获取促销列表"""
        response = api.get_promotions()
        assert response.status_code == 200
        data = response.json()
        assert "promotions" in data
        assert len(data["promotions"]) > 0

    def test_get_promotion_by_id(self, api):
        """测试获取促销详情"""
        response = api.get_promotion(1)
        assert response.status_code == 200
        promo = response.json()
        assert promo["id"] == 1
        assert "discount_type" in promo

    def test_dataclass_promotion_calculation(self):
        """测试促销数据类计算"""
        # 百分比折扣
        promo1 = Promotion(
            id=1,
            name="9折优惠",
            discount_type="percentage",
            discount_value=10,
            min_amount=100
        )

        assert promo1.calculate_discount(1000) == 100  # 1000 * 10%
        assert promo1.calculate_discount(50) == 0  # 不满足最低金额

        # 固定金额折扣
        promo2 = Promotion(
            id=2,
            name="满100减20",
            discount_type="fixed",
            discount_value=20,
            min_amount=100
        )

        assert promo2.calculate_discount(150) == 20
        assert promo2.calculate_discount(80) == 0


# ========== 订单测试 ==========
class TestOrders:
    """订单功能测试"""

    def test_create_order_without_promotion(self, api, user_id):
        """测试创建无促销订单"""
        # 先添加商品到购物车
        api.add_to_cart(user_id, product_id=1, quantity=1)

        # 创建订单
        response = api.create_order(user_id)
        assert response.status_code == 201
        order = response.json()
        assert order["user_id"] == user_id
        assert order["total"] == order["subtotal"]  # 无折扣
        assert order["status"] == "pending"

    def test_create_order_with_promotion(self, api):
        """测试创建带促销的订单"""
        user_id = 1002

        # 添加商品到购物车
        api.add_to_cart(user_id, product_id=2, quantity=1)  # 12999元商品

        # 使用促销创建订单
        response = api.create_order(user_id, promotion_id=1)  # 满1000减100
        assert response.status_code == 201
        order = response.json()
        assert order["discount"] > 0
        assert order["total"] < order["subtotal"]

    def test_get_order(self, api):
        """测试获取订单"""
        user_id = 1003
        api.add_to_cart(user_id, product_id=3, quantity=1)
        create_response = api.create_order(user_id)
        order_id = create_response.json()["id"]

        response = api.get_order(order_id)
        assert response.status_code == 200
        order = response.json()
        assert order["id"] == order_id

    def test_create_order_empty_cart(self, api):
        """测试空购物车创建订单"""
        response = api.create_order(9999)
        assert response.status_code == 400


# ========== 集成测试 ==========
class TestIntegration:
    """端到端集成测试"""

    def test_complete_shopping_flow(self, api):
        """测试完整购物流程"""
        user_id = 2001

        # 1. 浏览商品
        products_response = api.get_products()
        assert products_response.status_code == 200

        # 2. 添加商品到购物车
        api.add_to_cart(user_id, product_id=1, quantity=2)
        api.add_to_cart(user_id, product_id=3, quantity=1)

        # 3. 查看购物车
        cart_response = api.get_cart(user_id)
        assert cart_response.status_code == 200
        cart = cart_response.json()
        assert len(cart["items"]) == 2

        # 4. 查看促销
        promotions_response = api.get_promotions()
        assert promotions_response.status_code == 200

        # 5. 创建订单
        order_response = api.create_order(user_id, promotion_id=2)
        assert order_response.status_code == 201
        order = order_response.json()

        # 6. 验证订单
        assert order["total"] > 0
        assert "created_at" in order

        # 7. 验证购物车已清空
        cart_after = api.get_cart(user_id).json()
        assert len(cart_after["items"]) == 0