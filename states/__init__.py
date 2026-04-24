from aiogram.fsm.state import State, StatesGroup


class AddAdminStates(StatesGroup):
    waiting_for_tg_id = State()


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    confirm = State()
