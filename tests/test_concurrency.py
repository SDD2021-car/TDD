import concurrent.futures
import os
import sys
from typing import List

import pytest
from fastapi import HTTPException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api import ecommerce_api


@pytest.fixture(autouse=True)
def reset_state():
    ecommerce_api.reset_state()
    yield


def _add_to_cart(user_id: int) -> bool:
    try:
        ecommerce_api.add_to_cart(
            user_id,
            ecommerce_api.CartItemAdd(product_id=1, quantity=1),
            current_user=ecommerce_api.users_db["user1001"],
        )
        return True
    except HTTPException:
        return False


def _place_order(user_id: int):
    try:
        return ecommerce_api.create_order(
            ecommerce_api.OrderCreate(user_id=user_id),
            current_user=ecommerce_api.users_db["user1001"],
        )
    except HTTPException:
        return None


def test_concurrent_cart_addition_and_order_creation():
    """并发压力测试：模拟多用户同时加购和下单，验证锁的原子性。"""

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        add_results: List[bool] = list(executor.map(_add_to_cart, [1001] * 60))

    assert sum(add_results) == ecommerce_api.products_db[1]["stock"]
    assert ecommerce_api.products_db[1]["reserved"] == ecommerce_api.products_db[1]["stock"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        order_results = list(executor.map(_place_order, [1001] * 60))

    success_orders = [order for order in order_results if order is not None]
    assert len(success_orders) == 1
    assert ecommerce_api.products_db[1]["stock"] == 0
    assert ecommerce_api.products_db[1]["reserved"] == 0
    assert ecommerce_api.carts_db[1001]["items"] == []
    assert len(ecommerce_api.orders_db) == 1