from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    excursion_choice_date_from = State()
    excursion_choice_date_to = State()
    excursion_edit_property = State()
    timetable = State()