import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from threading import Lock

import pytest
from pydantic import BaseModel, Field
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
import base64
import hashlib
import hmac
from contextlib import redirect_stdout, redirect_stderr
import html
import io
import json
import time
from pathlib import Path
from trace import Trace

"""
电商测试API，实现基础的商品、购物车、促销和订单接口1
实现简单的鉴权与鉴权检查，防止用户越权访问其他用户的资源，同时限制敏感操作例如商品管理，仅管理员可用
"""
app = FastAPI(title="电商测试API")

STATIC_DIR = Path(__file__).parent.parent / "assets"
COVERAGE_DIR = Path(__file__).parent.parent / "coverage_html"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/coverage", StaticFiles(directory=COVERAGE_DIR, html=True), name="coverage")
SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24*60
bearer_scheme = HTTPBearer(auto_error=False)

BASE_PRODUCTS: Dict[int, dict] = {
    1: {"id": 1, "name": "iPhone 15", "price": 5999.0, "stock": 50, "category": "电子产品"},
    2: {"id": 2, "name": "MacBook Pro", "price": 12999.0, "stock": 30, "category": "电子产品"},
    3: {"id": 3, "name": "AirPods Pro", "price": 1899.0, "stock": 100, "category": "配件"},
}
products_db: Dict[int, dict] = {pid: product.copy() for pid, product in BASE_PRODUCTS.items()}

carts_db: Dict[int, dict] = {}
promotions_db: Dict[int, dict] = {
    1: {"id": 1, "name": "满1000减100", "discount_type": "fixed", "discount_value": 100, "min_amount": 1000},
    2: {"id": 2, "name": "全场9折", "discount_type": "percentage", "discount_value": 10, "min_amount": 0},
}
orders_db: Dict[int, dict] = {}
order_counter = 1
# 设置简单的用户与令牌映射，便于接口鉴权演示
users_db: Dict[str, dict] = {
    "admin": {"user_id": 1, "role": "admin", "name": "Admin", "password": "adminpass"},
    "user1001": {"user_id": 1001, "role": "user", "name": "Test User 1001", "password": "pass1001"},
    "user1002": {"user_id": 1002, "role": "user", "name": "Test User 1002", "password": "pass1002"},
    "user1003": {"user_id": 1003, "role": "user", "name": "Test User 1003", "password": "pass1003"},
    "user2001": {"user_id": 2001, "role": "user", "name": "Test User 2001", "password": "pass2001"},
}


# Pydantic 模型
class ProductCreate(BaseModel):
    name: str = Field(..., description="商品名称")
    price: float = Field(..., gt=0, description="商品价格，必须大于0")
    stock: int = Field(..., ge=0, description="库存数量，必须为非负整数")
    category: str = Field(..., description="商品分类")


class CartItemAdd(BaseModel):
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., gt=0, description="数量，必须大于0")


class OrderCreate(BaseModel):
    user_id: int
    promotion_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})
    header = {"alg": ALGORITHM, "typ": "JWT"}

    def _b64(data_bytes: bytes) -> str:
        return base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode()

    header_segment = _b64(json.dumps(header, separators=(",", ":")).encode())
    payload_segment = _b64(json.dumps(to_encode, separators=(",", ":")).encode())
    signing_input = f"{header_segment}.{payload_segment}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    signature_segment = _b64(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode_access_token(token: str) -> dict:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication information is incorrect")

    def _b64decode(data: str) -> bytes:
        padding = '=' * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    signing_input = f"{header_segment}.{payload_segment}".encode()
    expected_signature = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    try:
        signature = _b64decode(signature_segment)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication information is incorrect")
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication information is incorrect")

    payload_bytes = _b64decode(payload_segment)
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication information is incorrect")

    exp = payload.get("exp")
    if exp is None or time.time() > float(exp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired")
    return payload


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authentication information")
    token = credentials.credentials if hasattr(credentials, "credentials") else str(credentials)
    payload = decode_access_token(token)
    username: Optional[str] = payload.get("sub")
    if username is None or username not in users_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication information is incorrect")
    return users_db[username]


def ensure_admin(current_user: dict) -> None:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="need admin role",
        )


def ensure_owner_or_admin(target_user_id: int, current_user: dict) -> None:
    """确保访问的user_id与当前用户匹配，或当前用户为管理员"""
    if current_user.get("role") == "admin":
        return
    if current_user.get("user_id") != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you are not allowed to access this resource",
        )


@app.post("/api/auth/token", response_model=TokenResponse)
def login(request: LoginRequest):
    user = users_db.get(request.username)
    if user is None or user.get("password") != request.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password")
    token = create_access_token({"sub": request.username, "role": user["role"], "uid": user["user_id"]})
    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


# ========== 商品接口 ==========
@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/products")
def get_products(
        category: Optional[str] = None,
        current_user: dict = Depends(get_current_user)):
    products = list(products_db.values())
    if category:
        products = [p for p in products if p["category"] == category]
    return {"products": products, "count": len(products)}


@app.get("/api/products/{product_id}")
def get_product(
        product_id: int,
        current_user: dict = Depends(get_current_user),
):
    """获取单个商品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    return products_db[product_id]


@app.post("/api/products", status_code=201)
def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """创建商品"""
    ensure_admin(current_user)
    product_id = max(products_db.keys()) + 1 if products_db else 1
    new_product = {"id": product_id, **product.model_dump()}
    products_db[product_id] = new_product
    return new_product


@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """更新商品"""
    ensure_admin(current_user)
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    products_db[product_id].update(product.model_dump())
    return products_db[product_id]


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, current_user: dict = Depends(get_current_user)):
    """删除商品"""
    ensure_admin(current_user)
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    del products_db[product_id]
    return {"message": "删除成功"}


# ========== 购物车接口 ==========
@app.get("/api/cart/{user_id}")
def get_cart(user_id: int, current_user: dict = Depends(get_current_user)):
    """获取购物车"""
    ensure_owner_or_admin(user_id, current_user)
    cart = carts_db.get(user_id, {"user_id": user_id, "items": []})
    total = sum(item["quantity"] * item["price"] for item in cart.get("items", []))
    cart_with_total = {**cart, "total": total}
    carts_db[user_id] = cart_with_total
    return cart_with_total


@app.post("/api/cart/{user_id}/items")
def add_to_cart(user_id: int, item: CartItemAdd, current_user: dict = Depends(get_current_user)):
    """添加商品到购物车"""
    ensure_owner_or_admin(user_id, current_user)
    if item.product_id not in products_db:
        raise HTTPException(status_code=404, detail="商品不存在")

    product = products_db[item.product_id]
    if product["stock"] < item.quantity:
        raise HTTPException(status_code=400, detail="库存不足")

    carts_db.setdefault(user_id, {"user_id": user_id, "items": []})
    cart = carts_db[user_id]
    for cart_item in cart["items"]:
        if cart_item["product_id"] == item.product_id:
            cart_item["quantity"] += item.quantity
            break
    else:
        cart["items"].append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "quantity": item.quantity,
            "price": product["price"],
        })
    return cart


@app.delete("/api/cart/{user_id}/items/{product_id}")
def remove_from_cart(user_id: int, product_id: int, current_user: dict = Depends(get_current_user)):
    """从购物车移除商品"""
    ensure_owner_or_admin(user_id, current_user)
    if user_id not in carts_db:
        raise HTTPException(status_code=404, detail="购物车不存在")
    cart = carts_db[user_id]
    for index, item in enumerate(cart["items"]):
        if item["product_id"] == product_id:
            cart["items"].pop(index)
            return cart

    raise HTTPException(status_code=404, detail="Product not found in the cart")


# ========== 促销接口 ==========
@app.get("/api/promotions")
def get_promotions(current_user: dict = Depends(get_current_user)):
    """获取促销列表"""
    return {"promotions": list(promotions_db.values())}


@app.get("/api/promotions/{promotion_id}")
def get_promotion(promotion_id: int, current_user: dict = Depends(get_current_user)):
    """获取促销详情"""
    if promotion_id not in promotions_db:
        raise HTTPException(status_code=404, detail="促销不存在")
    return promotions_db[promotion_id]


# ========== 订单接口 ==========
# 业务逻辑测试
# 计算购物车中的商品的小计金额，判断优惠形式并计算折扣金额
@app.post("/api/orders", status_code=201)
def create_order(order: OrderCreate, current_user: dict = Depends(get_current_user)):
    """创建订单"""
    ensure_owner_or_admin(order.user_id, current_user)

    if order.user_id not in carts_db or not carts_db[order.user_id]["items"]:
        raise HTTPException(status_code=400, detail="购物车为空")

    cart = carts_db[order.user_id]
    subtotal = sum(item["quantity"] * item["price"] for item in cart["items"])

    discount = 0.0
    if order.promotion_id and order.promotion_id in promotions_db:
        promo = promotions_db[order.promotion_id]
        if subtotal >= promo["min_amount"]:
            if promo["discount_type"] == "percentage":
                discount = subtotal * (promo["discount_value"] / 100)
            elif promo["discount_type"] == "fixed":
                discount = min(promo["discount_value"], subtotal)

    total = max(subtotal - discount, 0)
    global order_counter
    order_id = order_counter
    order_counter += 1
    new_order = {
        "id": order_id,
        "user_id": order.user_id,
        "items": cart["items"].copy(),
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    orders_db[order_id] = new_order
    # 清空购物车
    carts_db[order.user_id] = {"user_id": order.user_id, "items": []}
    return new_order


@app.get("/api/orders/{order_id}")
def get_order(order_id: int, current_user: dict = Depends(get_current_user)):
    """获取订单详情"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="订单不存在")
    order = orders_db[order_id]
    ensure_owner_or_admin(order["user_id"], current_user)
    return order


def calculate_discount(amount: float, promotion: Dict) -> float:
    """根据促销类型计算折扣"""
    discount_type = promotion["discount_type"]
    discount_value = promotion["discount_value"]
    min_amount = promotion.get("min_amount", 0)
    if amount < min_amount:
        return 0.0
    if discount_type == "percentage":
        return amount * promotion["discount_value"] / 100
    if discount_type == "fixed":
        return min(discount_value, amount)
    return 0.0


def reset_state() -> None:
    products_db.clear()
    products_db.update({pid: product.copy() for pid, product in BASE_PRODUCTS.items()})
    carts_db.clear()
    orders_db.clear()
    global order_counter
    order_counter = 1


def _calculate_trace_coverage(results) -> Optional[float]:
    project_root = Path(__file__).parent.parent.resolve()
    file_hits: Dict[Path, Dict[int, int]] = {}

    for (filename, lineno), count in results.counts.items():
        path = Path(filename).resolve()
        if project_root not in path.parents:
            continue
        file_hits.setdefault(path, {})[lineno] = count

    total_lines = 0
    executed_lines = 0
    for path, line_hits in file_hits.items():
        try:
            file_lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        total_lines += len(file_lines)
        executed_lines += sum(1 for lineno in range(1, len(file_lines) + 1) if line_hits.get(lineno, 0) > 0)

    if total_lines == 0:
        return None
    return round(executed_lines / total_lines * 100, 2)


@app.get("/test_dashboard")
def serve_test_dashboard():
    dashboard_path = STATIC_DIR / "test_dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return HTMLResponse("<h1>Test dashboard not found</h1>", status_code=404)


@app.post("/api/tests/run")
def run_tests():
    tracer = Trace(count=True, trace=False, infile=None, outfile=None)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result_code = tracer.runfunc(pytest.main, ["-q"])

    results = tracer.results()
    results.write_results(show_missing=True, summary=True, coverdir=str(COVERAGE_DIR))
    coverage_percent = _calculate_trace_coverage(results)
    coverage_report = COVERAGE_DIR / "index.html"
    coverage_report.write_text(
        f"""
        <html><body>
        <h1>测试覆盖率</h1>
        <p>覆盖率: {coverage_percent if coverage_percent is not None else '未知'}%</p>
        <h2>Pytest 输出</h2>
        <pre>{html.escape(stdout_buffer.getvalue())}</pre>
        <h2>Pytest 错误</h2>
        <pre>{html.escape(stderr_buffer.getvalue())}</pre>
        </body></html>
        """
    )

    response = {
        "return_code": result_code,
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_buffer.getvalue(),
        "coverage_percent": f"{coverage_percent}%" if coverage_percent is not None else None,
        "coverage_report": "/coverage/index.html",
    }
    if result_code == 0:
        return response
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.ecommerce_api:app", host="0.0.0.0", port=8000, reload=False)
