pizzas = {"pepperoni": "Пепперони", "chili": "Чили", "4seasons": "4 сезона"}
snacks = {
    "roll-caesar": "Цезарь ролл",
    "roll-fish": "Ролл с лососем",
}
drinks = ["Coca-Cola", "Fanta", "Sprite"]


class Product:
    def __init__(self, name: str, callback_name: str, category: str):
        self.name = name
        self.callback_name = callback_name
        self.category = category


products = []

for callback_name, name in pizzas.items():
    products.append(
        Product(
            name=name,
            callback_name=callback_name,
            category="pizza",
        )
    )
    # products.append(
    #     Product(
    #         name=name,
    #         size="Большая (35 см)",
    #         callback_name=callback_name,
    #         category="pizza",
    #     )
    # )

for callback_name, name in snacks.items():
    products.append(
        Product(
            name=name,
            callback_name=callback_name,
            category="snack",
        )
    )

for name in drinks:
    products.append(
        Product(
            name=name,
            callback_name=name.lower(),
            category="drink",
        )
    )
    # products.append(
    #     Product(
    #         name=name,
    #         size="0,5 литра",
    #         callback_name=name.lower().replace("-", "_"),
    #         category="drink",
    #     )
    # )

# for i in products:
#     print(i.name, i.callback_name, i.category, i.size)

# from typing import List
# def abc(products:List[Product]):
#     for i in products:
#         if i.callback_name == 'pepperoni':
#             print(i.name)
# abc(products)
