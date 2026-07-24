from aiogram.fsm.state import State, StatesGroup


class AddCategory(StatesGroup):
    name = State()


class AddProduct(StatesGroup):
    category = State()
    title = State()
    description = State()
    price = State()
    photo = State()


class EditProduct(StatesGroup):
    choose_product = State()
    choose_field = State()
    new_value = State()


class Broadcast(StatesGroup):
    text = State()
    confirm = State()

