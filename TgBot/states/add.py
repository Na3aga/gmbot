from aiogram.dispatcher.filters.state import StatesGroup, State


class AddGmail(StatesGroup):
    Add = State()
    AccountCheck = State()
