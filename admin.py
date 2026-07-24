import os

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from config import ADMIN_IDS, FILES_DIR
from states import AddCategory, AddProduct, Broadcast, EditProduct

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 Админ-панель", reply_markup=kb.admin_menu_kb())


@router.callback_query(F.data == "adm:menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.answer("🔧 Админ-панель", reply_markup=kb.admin_menu_kb())
    await callback.answer()


# ---------- ДОБАВЛЕНИЕ КАТЕГОРИИ ----------

@router.callback_query(F.data == "adm:add_cat")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AddCategory.name)
    await callback.message.answer("Введите название новой категории:")
    await callback.answer()


@router.message(AddCategory.name)
async def add_category_finish(message: Message, state: FSMContext):
    await db.add_category(message.text.strip())
    await state.clear()
    await message.answer(f"✅ Категория «{message.text.strip()}» добавлена.", reply_markup=kb.admin_menu_kb())


# ---------- СПИСОК КАТЕГОРИЙ ----------

@router.callback_query(F.data == "adm:list_cat")
async def list_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    categories = await db.get_categories()
    if not categories:
        await callback.message.answer("Категорий пока нет.", reply_markup=kb.admin_menu_kb())
        await callback.answer()
        return
    text = "🗂 Категории:\n\n" + "\n".join(f"{c['id']}. {c['name']}" for c in categories)
    await callback.message.answer(text, reply_markup=kb.admin_menu_kb())
    await callback.answer()


# ---------- ДОБАВЛЕНИЕ ТОВАРА ----------

@router.callback_query(F.data == "adm:add_prod")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    categories = await db.get_categories()
    if not categories:
        await callback.message.answer(
            "Сначала добавьте хотя бы одну категорию.", reply_markup=kb.admin_menu_kb()
        )
        await callback.answer()
        return
    await state.set_state(AddProduct.category)
    await callback.message.answer(
        "Выберите категорию для нового товара:",
        reply_markup=kb.admin_categories_kb(categories, "adm_new_prod_cat"),
    )
    await callback.answer()


@router.callback_query(AddProduct.category, F.data.startswith("adm_new_prod_cat:"))
async def add_product_category_chosen(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(AddProduct.title)
    await callback.message.answer("Введите название сборки:")
    await callback.answer()


@router.message(AddProduct.title)
async def add_product_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddProduct.description)
    await message.answer("Введите описание сборки:")


@router.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddProduct.price)
    await message.answer("Введите цену в рублях (только число):")


@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Введите цену числом, например: 499")
        return
    await state.update_data(price_rub=int(message.text.strip()))
    await state.set_state(AddProduct.file)
    await message.answer("Пришлите файл сборки (архив .zip) как документ:")


@router.message(AddProduct.file, F.document)
async def add_product_file(message: Message, state: FSMContext, bot: Bot):
    os.makedirs(FILES_DIR, exist_ok=True)
    data = await state.get_data()
    safe_name = data["title"].lower().replace(" ", "_")
    file_path = os.path.join(FILES_DIR, f"{safe_name}_{message.document.file_id[:8]}.zip")
    await bot.download(message.document, destination=file_path)
    await state.update_data(file_path=file_path)
    await state.set_state(AddProduct.photo)
    await message.answer("Пришлите превью-фото (или отправьте /skip, чтобы пропустить):")


@router.message(AddProduct.file)
async def add_product_file_invalid(message: Message):
    await message.answer("Пришлите именно файл (документ), например .zip архив.")


@router.message(AddProduct.photo, Command("skip"))
async def add_product_skip_photo(message: Message, state: FSMContext):
    await finish_add_product(message, state, photo_path="")


@router.message(AddProduct.photo, F.photo)
async def add_product_photo(message: Message, state: FSMContext, bot: Bot):
    os.makedirs(FILES_DIR, exist_ok=True)
    data = await state.get_data()
    safe_name = data["title"].lower().replace(" ", "_")
    photo_path = os.path.join(FILES_DIR, f"{safe_name}_preview.jpg")
    await bot.download(message.photo[-1], destination=photo_path)
    await finish_add_product(message, state, photo_path=photo_path)


async def finish_add_product(message: Message, state: FSMContext, photo_path: str):
    data = await state.get_data()
    await db.add_product(
        category_id=data["category_id"],
        title=data["title"],
        description=data["description"],
        price_rub=data["price_rub"],
        file_path=data.get("file_path", ""),
        photo_path=photo_path,
    )
    await state.clear()
    await message.answer(f"✅ Товар «{data['title']}» добавлен в каталог!", reply_markup=kb.admin_menu_kb())


# ---------- СПИСОК / РЕДАКТИРОВАНИЕ / УДАЛЕНИЕ ТОВАРОВ ----------

@router.callback_query(F.data == "adm:list_prod")
async def list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    products = await db.get_all_products()
    if not products:
        await callback.message.answer("Товаров пока нет.", reply_markup=kb.admin_menu_kb())
        await callback.answer()
        return
    for p in products:
        status = "✅" if p["is_active"] else "🚫"
        text = f"{status} <b>{p['title']}</b> — {p['price_rub']}₽\n{p['description'][:100]}"
        await callback.message.answer(text, reply_markup=kb.admin_product_actions_kb(p["id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_edit:"))
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    _, product_id, field = callback.data.split(":")
    await state.update_data(product_id=int(product_id), field=field)
    await state.set_state(EditProduct.new_value)
    field_names = {"title": "название", "description": "описание", "price_rub": "цену"}
    await callback.message.answer(f"Введите новое значение ({field_names.get(field, field)}):")
    await callback.answer()


@router.message(EditProduct.new_value)
async def edit_product_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    value = message.text.strip()
    if field == "price_rub":
        if not value.isdigit():
            await message.answer("Введите цену числом.")
            return
        value = int(value)
    await db.update_product_field(data["product_id"], field, value)
    await state.clear()
    await message.answer("✅ Товар обновлён.", reply_markup=kb.admin_menu_kb())


@router.callback_query(F.data.startswith("adm_del_prod:"))
async def delete_product_confirm(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await callback.message.answer(
        "Точно удалить этот товар?", reply_markup=kb.confirm_kb("adm_del_prod", product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_del_prod_yes:"))
async def delete_product_execute(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await db.delete_product(product_id)
    await callback.message.answer("🗑 Товар удалён.", reply_markup=kb.admin_menu_kb())
    await callback.answer()


# ---------- СТАТИСТИКА ----------

@router.callback_query(F.data == "adm:stats")
async def show_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = await db.get_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"Пользователей: {stats['users_count']}\n"
        f"Заказов: {stats['orders_count']}\n"
        f"Выручка: {stats['revenue']}₽"
    )
    await callback.message.answer(text, reply_markup=kb.admin_menu_kb())
    await callback.answer()


# ---------- РАССЫЛКА ----------

@router.callback_query(F.data == "adm:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(Broadcast.text)
    await callback.message.answer("Введите текст рассылки для всех пользователей:")
    await callback.answer()


@router.message(Broadcast.text)
async def broadcast_finish(message: Message, state: FSMContext, bot: Bot):
    user_ids = await db.get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            failed += 1
    await state.clear()
    await message.answer(
        f"📢 Рассылка завершена.\nОтправлено: {sent}\nНе доставлено: {failed}",
        reply_markup=kb.admin_menu_kb(),
    )
