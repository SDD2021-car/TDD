from dataclasses import dataclass,field
from typing import List,Optional
from datetime import datetime

@dataclass
class Product:
    # 商品数据类
    id:int
    name:str
    price:float
    stock:int
    category:str
    description: Optional[str] = None

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price must be greater than 0")
        if self.stock < 0:
            raise ValueError("Stock must be greater than 0")

@dataclass
class CartItem:
    # 购物车商品
    product_id:int
    product_name:str
    quantity:int
    price:float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.price

@dataclass
class ShoppingCart:
    # 购物车数据类
    user_id:int
    items:List[CartItem] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def add_item(self,item:CartItem):
        # 添加商品到购物车
        for existing_item in self.items:
            if existing_item.product_id == item.product_id:
                existing_item.quantity += item.quantity
                return
        self.items.append(item)

    def remove_item(self, product_id:int):
        # 从购物车移除商品
        self.items = [item for item in self.items if item.product_id != product_id]

@dataclass
class Promotion:
    # 促销策略类
    id:int
    name:str
    discount_type:str
    discount_value:float
    min_amount: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def calculate_discount(self, amount:float) -> float:
        # 计算折扣金额
        if amount < self.min_amount:
            return 0.0
        if self.discount_type == "percentage":
            return amount * (self.discount_value / 100)
        elif self.discount_type == "fixed":
            return min(self.discount_value, amount)
        return 0.0

@dataclass
class Order:
    # 订单数据类
    id: int
    user_id:int
    items:List[CartItem]
    subtotal:float
    discount:float
    total: float
    status:str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

