from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    excursion_choice_date = State()
    excursion_edit_date = State()
    excursion_edit_property = State()
    excursion_people_edit = State()
    timetable = State()
    excursion_food_amount = State()
    excursion_food_name = State()