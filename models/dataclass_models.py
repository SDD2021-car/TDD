"""
    模拟电商业务场景：
    商品：product
    购物车： cart
    单项商品： cart item
    促销： promotion
    订单： order
    @dataclass 用于定义数据类，简化class编写
"""
from dataclasses import dataclass,field
from typing import List,Optional
from datetime import datetime

@dataclass
class Product:
    # 商品数据类 存储商品信息
    # 描述商品信息，并在初始化时校验商品设置合法性
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
    # 购物车中某一项商品
    product_id:int    #商品Id
    product_name:str    # 商品名
    quantity:int    # 商品数量
    price:float     # 商品单价

    @property
    def subtotal(self) -> float:
        # 商品金额小计
        return self.quantity * self.price

@dataclass
class ShoppingCart:
    # 属于聚合根
    # 购物车数据类 用户购物车
    user_id:int     # 用户Id
    items:List[CartItem] = field(default_factory=list)  # 包含的每一个商品

    @property
    def total(self) -> float:
        # 金额总计
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
    # 促销策略类 采用百分比/固定金额
    id:int      # 促销策略ID
    name:str    # 促销策略名
    discount_type:str   # 促销类型
    discount_value:float    # 折扣力度，随促销类型改变而改变
    min_amount: float = 0.0     # 触发促销的最低消费金额
    start_date: Optional[datetime] = None   # 促销开始时间
    end_date: Optional[datetime] = None     # 促销结束时间

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
    # 订单数据类 最终订单
    id: int
    user_id:int
    items:List[CartItem]
    subtotal:float
    discount:float
    total: float
    status:str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

