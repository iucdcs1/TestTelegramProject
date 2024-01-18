from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    excursion_choice_date = State()
    excursion_edit_property = State()
    timetable = State()