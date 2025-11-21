from typing import List, Dict, Optional
from datetime import datetime
from threading import Lock
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
"""
电商测试API，实现基础的商品、购物车、促销和订单接口
实现简单的鉴权与鉴权检查，防止用户越权访问其他用户的资源，同时限制敏感操作例如商品管理，仅管理员可用
"""
app = FastAPI(title="电商测试API")

# 内存数据库
# 测试数据设计 预置了几种商品，以及两种促销方式
products_db: Dict[int, dict] = {
    1: {"id": 1, "name": "iPhone 15", "price": 5999.0, "stock": 50, "category": "电子产品"},
    2: {"id": 2, "name": "MacBook Pro", "price": 12999.0, "stock": 30, "category": "电子产品"},
    3: {"id": 3, "name": "AirPods Pro", "price": 1899.0, "stock": 100, "category": "配件"},
}

carts_db: Dict[int, dict] = {}
promotions_db: Dict[int, dict] = {
    1: {"id": 1, "name": "满1000减100", "discount_type": "fixed", "discount_value": 100, "min_amount": 1000},
    2: {"id": 2, "name": "全场9折", "discount_type": "percentage", "discount_value": 10, "min_amount": 0},
}
orders_db: Dict[int, dict] = {}
order_counter = 1
db_lock = Lock()

# 设置简单的用户与令牌映射，便于接口鉴权演示
users_db: Dict[str, dict] = {
    "admin-token": {"user_id" : 1, "role": "admin", "name": "Admin"},
    "user-1001-token": {"user_id" : 1001, "role": "user", "name": "Test User 1001"},
    "user-1002-token": {"user_id" : 1002, "role": "user", "name": "Test User 1002"},
    "user-1003-token": {"user_id" : 1003, "role": "user", "name": "Test User 1003"},
    "user-2001-token": {"user_id" : 2001, "role": "user", "name": "Test User 2001"},
}
# HTTP Bearer 安全方案
bearer_scheme = HTTPBearer(auto_error=False)

# Pydantic 模型
class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int
    category: str

class CartItemAdd(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    user_id: int
    promotion_id: Optional[int] = None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
        根据Authorization Bearer Token 获取当前用户信息
        当token无效或缺失，抛出401，确保所有业务接口都有身份凭证
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing authentication information",
        )
    token = credentials.credentials
    if token not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication information is incorrect",
        )
    return users_db[token]

def ensure_admin(current_user:dict) -> dict:
    """仅允许管理员执行的操作，非管理员抛出异常403"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_UNAUTHORIZED,
            detail="need admin role",
        )

def ensure_owner_or_admin(target_user_id:int, current_user:dict) -> None:
    """确保访问的user_id与当前用户匹配，或当前用户为管理员"""
    if current_user.get("role") == "admin":
        return
    if current_user.get("user_id") != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_UNAUTHORIZED,
            detail="you are not allowed to access this resource",
        )

# ========== 商品接口 ==========
@app.get("/")
def root(current_user:dict = Depends(get_current_user)):
    return {"message": "电商测试API运行中", "version": "1.0", "user": current_user.get("name")}

@app.get("/api/products")
def get_products(
        category: Optional[str] = None,
        current_user:dict = Depends(get_current_user),
):
    """获取商品列表"""
    products = list(products_db.values())
    if category:
        products = [p for p in products if p["category"] == category]
    return {"products": products, "count": len(products)}


@app.get("/api/products/{product_id}")
def get_product(
        product_id: int,
        current_user:dict = Depends(get_current_user),
):
    """获取单个商品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    return products_db[product_id]


@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate, current_user:dict = Depends(get_current_user)):
    """创建商品"""
    ensure_admin(current_user)
    with db_lock:
        product_id = max(products_db.keys()) + 1 if products_db else 1
        new_product = {
            "id": product_id,
            **product.dict()
        }
        products_db[product_id] = new_product
        return new_product


@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: ProductCreate, current_user:dict = Depends(get_current_user)):
    """更新商品"""
    ensure_admin(current_user)
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    with db_lock:
        products_db[product_id].update(product.dict())
        return products_db[product_id]


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, current_user:dict = Depends(get_current_user)):
    """删除商品"""
    ensure_admin(current_user)
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    with db_lock:
        del products_db[product_id]
        return {"message": "删除成功"}


# ========== 购物车接口 ==========
@app.get("/api/cart/{user_id}")
def get_cart(user_id: int, current_user: dict = Depends(get_current_user)):
    """获取购物车"""
    ensure_owner_or_admin(user_id, current_user)
    cart = carts_db.get(user_id, {"user_id": user_id, "items": []})
    total = sum(item["quantity"] * item["price"] for item in cart["items"])
    return {**cart, "total": total}

@app.post("/api/cart/{user_id}/items")
def add_to_cart(user_id: int, item: CartItemAdd, current_user:dict = Depends(get_current_user),):
    """添加商品到购物车"""
    ensure_owner_or_admin(user_id, current_user)
    if item.product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")

    product = products_db[item.product_id]
    if product["stock"] < item.quantity:
        raise HTTPException(status_code=400, detail="库存不足")

    with db_lock:
        if user_id not in carts_db:
            carts_db[user_id] = {"user_id": user_id, "items": []}

        cart = carts_db[user_id]
        for cart_item in cart["items"]:
            if cart_item["product_id"] == item.product_id:
                cart_item["quantity"] += item.quantity
                return cart

        cart["items"].append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "quantity": item.quantity,
            "price": product["price"]
        })
        return cart


@app.delete("/api/cart/{user_id}/items/{product_id}")
def remove_from_cart(user_id: int, product_id: int, current_user:dict = Depends(get_current_user),):
    """从购物车移除商品"""
    ensure_owner_or_admin(user_id, current_user)
    if user_id not in carts_db:
        raise HTTPException(status_code=404, detail="购物车不存在")
    with db_lock:
        cart = carts_db[user_id]
        cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
        return cart


# ========== 促销接口 ==========
@app.get("/api/promotions")
def get_promotions(current_user:dict = Depends(get_current_user)):
    """获取促销列表"""
    return {"promotions": list(promotions_db.values())}

@app.get("/api/promotions/{promotion_id}")
def get_promotion(promotion_id: int, current_user:dict = Depends(get_current_user)):
    """获取促销详情"""
    if promotion_id not in promotions_db:
        raise HTTPException(status_code=404, detail="促销不存在")
    return promotions_db[promotion_id]


# ========== 订单接口 ==========
# 业务逻辑测试
# 计算购物车中的商品的小计金额，判断优惠形式并计算折扣金额
@app.post("/api/orders", status_code=201)
def create_order(order_create: OrderCreate, current_user:dict = Depends(get_current_user)):
    """创建订单"""
    global order_counter

    ensure_owner_or_admin(order_create.user_id, current_user)

    if order_create.user_id not in carts_db or not carts_db[order_create.user_id]["items"]:
        raise HTTPException(status_code=400, detail="购物车为空")

    cart = carts_db[order_create.user_id]
    subtotal = sum(item["quantity"] * item["price"] for item in cart["items"])

    discount = 0.0
    if order_create.promotion_id and order_create.promotion_id in promotions_db:
        promo = promotions_db[order_create.promotion_id]
        if subtotal >= promo["min_amount"]:
            if promo["discount_type"] == "percentage":
                discount = subtotal * (promo["discount_value"] / 100)
            elif promo["discount_type"] == "fixed":
                discount = min(promo["discount_value"], subtotal)
    with db_lock:
        order = {
            "id": order_counter,
            "user_id": order_create.user_id,
            "items": cart["items"].copy(),
            "subtotal": subtotal,
            "discount": discount,
            "total": subtotal - discount,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        orders_db[order_counter] = order
        order_counter += 1

        # 清空购物车
        carts_db[order_create.user_id]["items"] = []

        return order


@app.get("/api/orders/{order_id}")
def get_order(order_id: int, current_user:dict = Depends(get_current_user)):
    """获取订单详情"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = orders_db[order_id]
    ensure_owner_or_admin(order["user_id"], current_user)
    return orders_db[order_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8800)