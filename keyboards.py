from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_kb(categories: list[dict]):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat["name"], callback_data=f"cat:{cat['id']}")
    builder.adjust(1)
    return builder.as_markup()


def products_kb(products: list[dict], category_id: int):
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['title']} — {product['price_rub']}₽",
            callback_data=f"product:{product['id']}",
        )
    builder.button(text="⬅️ Назад к категориям", callback_data="categories")
    builder.adjust(1)
    return builder.as_markup()


def product_card_kb(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Добавить в корзину", callback_data=f"add_cart:{product_id}")
    builder.button(text="⬅️ Назад", callback_data="categories")
    builder.adjust(1)
    return builder.as_markup()


def cart_kb(cart_items: list[dict]):
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        builder.button(
            text=f"❌ {item['title']} x{item['quantity']}",
            callback_data=f"remove_cart:{item['id']}",
        )
    if cart_items:
        builder.button(text="✅ Оформить заказ", callback_data="checkout")
        builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="⬅️ В меню", callback_data="categories")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить категорию", callback_data="adm:add_cat")
    builder.button(text="📂 Список категорий", callback_data="adm:list_cat")
    builder.button(text="➕ Добавить товар", callback_data="adm:add_prod")
    builder.button(text="📢 Рассылка", callback_data="adm:broadcast")
    builder.adjust(1)
    return builder.as_markup()


def admin_categories_kb(categories: list[dict], callback_prefix: str):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat["name"], callback_data=f"{callback_prefix}:{cat['id']}")
    builder.button(text="⬅️ Назад", callback_data="adm:menu")
    builder.adjust(1)
    return builder.as_markup()

