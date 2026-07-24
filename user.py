import os

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

import database as db
import keyboards as kb
from config import ADMIN_IDS, PROVIDER_TOKEN

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.register_user(message.from_user.id, message.from_user.username)
    categories = await db.get_categories()
    if not categories:
        await message.answer(
            "👋 Привет! Каталог пока пуст, загляните позже.\n\n"
            "(Админ: используйте /admin, чтобы добавить категории и товары)"
        )
        return
    await message.answer(
        "👋 Привет! Здесь можно купить готовые сборки серверов Minecraft.\n\n"
        "Выберите категорию:",
        reply_markup=kb.categories_kb(categories),
    )


@router.callback_query(F.data == "categories")
async def show_categories(callback: CallbackQuery):
    categories = await db.get_categories()
    await callback.message.answer("📂 Выберите категорию:", reply_markup=kb.categories_kb(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def show_category_products(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    products = await db.get_products_by_category(category_id)
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    await callback.message.answer(
        "📦 Товары в категории:", reply_markup=kb.products_kb(products, category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    text = f"<b>{product['title']}</b>\n\n{product['description']}\n\n💰 Цена: {product['price_rub']}₽"
    photo_path = product.get("photo_path") or ""

    if photo_path and os.path.exists(photo_path):
        await callback.message.answer_photo(
            FSInputFile(photo_path), caption=text, reply_markup=kb.product_card_kb(product_id)
        )
    else:
        await callback.message.answer(text, reply_markup=kb.product_card_kb(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("add_cart:"))
async def add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await db.add_to_cart(callback.from_user.id, product_id)
    await callback.answer("Добавлено в корзину ✅")


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    items = await db.get_cart(callback.from_user.id)
    if not items:
        await callback.message.answer("🛒 Корзина пуста")
        await callback.answer()
        return
    total = sum(i["price_rub"] for i in items)
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    for i in items:
        text += f"• {i['title']} — {i['price_rub']}₽\n"
    text += f"\n<b>Итого: {total}₽</b>"
    await callback.message.answer(text, reply_markup=kb.cart_kb(items))
    await callback.answer()


@router.callback_query(F.data.startswith("remove_cart:"))
async def remove_from_cart(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await db.remove_from_cart(callback.from_user.id, product_id)
    await callback.answer("Удалено из корзины")
    await show_cart(callback)


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, bot: Bot):
    items = await db.get_cart(callback.from_user.id)
    if not items:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    prices = [LabeledPrice(label=i["title"], amount=i["price_rub"] * 100) for i in items]
    payload = "cart:" + ",".join(str(i["id"]) for i in items)
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Оплата заказа",
        description=f"Товаров в заказе: {len(items)}",
        payload=payload,
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="cart-checkout",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_now:"))
async def buy_now(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    prices = [LabeledPrice(label=product["title"], amount=product["price_rub"] * 100)]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=product["title"],
        description=product["description"],
        payload=f"cart:{product_id}",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter=f"buy-{product_id}",
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot):
    payment = message.successful_payment
    product_ids = [int(x) for x in payment.invoice_payload.replace("cart:", "").split(",")]

    delivered = []
    for pid in product_ids:
        product = await db.get_product(pid)
        if product:
            delivered.append(product)

    await db.create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        items=delivered,
        charge_id=payment.telegram_payment_charge_id,
    )
    await db.clear_cart(message.from_user.id)

    await message.answer(f"✅ Оплата на сумму {payment.total_amount // 100}₽ прошла успешно! Высылаю файлы:")
    for product in delivered:
        file_path = product.get("file_path") or ""
        if file_path and os.path.exists(file_path):
            await message.answer_document(
                FSInputFile(file_path),
                caption=f"📦 {product['title']}",
            )
        else:
            await message.answer(
                f"⚠️ Файл для «{product['title']}» временно недоступен, напишите в поддержку."
            )

    for admin_id in ADMIN_IDS:
        try:
            names = ", ".join(p["title"] for p in delivered)
            await bot.send_message(
                admin_id,
                f"💰 Новая продажа!\nПокупатель: @{message.from_user.username} (id {message.from_user.id})\n"
                f"Товары: {names}\nСумма: {payment.total_amount // 100}₽",
            )
        except Exception:
            pass

