from typing import Dict, List

pizzas = {"pepperoni": "Пепперони", "chili": "Чили", "4seasons": "4 сезона"}
snacks = {
    "roll-caesar": "Цезарь ролл",
    "roll-fish": "Ролл с лососем",
}
drinks = ["Coca-Cola", "Fanta", "Sprite"]


class Product:
    def __init__(
        self,
        name: str,
        callback_name: str,
        category: str,
        price: float | Dict[str, float],
    ):
        self.name = name
        self.callback_name = callback_name
        self.category = category
        self.price = price

    def get_price(self):
        return self.price


products = []

for callback_name, name in pizzas.items():
    products.append(
        Product(
            name=name,
            callback_name=callback_name,
            category="pizza",
            price={"small": 22.15, "large": 30.55},
        )
    )


for callback_name, name in snacks.items():
    products.append(
        Product(name=name, callback_name=callback_name, category="snack", price=8.99)
    )

for name in drinks:
    products.append(
        Product(
            name=name,
            callback_name=name.lower(),
            category="drink",
            price={"small": 1.95, "large": 2.99},
        )
    )
