import datetime
import logging

from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from application.database.requests import get_excursions, get_user_excursions, get_week_excursions, get_users, get_user, \
    get_timetable, get_excursion, get_guide_list, get_user_by_id, get_month_excursions
from application.utilities.tools import compare_dates, time_intersecting, compare_time

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Экскурсии')],
    [KeyboardButton(text='Расписание')],
    [KeyboardButton(text='Профиль')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')

only_back = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Главная')]
], resize_keyboard=True, input_field_placeholder='')

only_back_properties = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Главная')]
], resize_keyboard=True, input_field_placeholder='Выберите поле или выберите пункт ниже')

main_admin = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Экскурсии')],
    [KeyboardButton(text='Расписание')],
    [KeyboardButton(text='Профиль')],
    [KeyboardButton(text='Админ-панель')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')

admin_panel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Изменение экскурсий'), KeyboardButton(text='Назначение')],
    [KeyboardButton(text='Просмотреть расписание'), KeyboardButton(text='Отчёт')],
    [KeyboardButton(text='Выгрузка экскурсий')], [KeyboardButton(text='Главная')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')

week_panel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Текущая неделя'), KeyboardButton(text='Текущий месяц')],
    [KeyboardButton(text='Весь период')],
    [KeyboardButton(text='Главная')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже или введите дату')

report_intervals = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отчёт за день'), KeyboardButton(text='Отчёт за неделю')],
    [KeyboardButton(text='Отчёт за месяц'), KeyboardButton(text='Общий отчёт')],
    [KeyboardButton(text='Вернуться')]
], resize_keyboard=True, input_field_placeholder='Выберите временной интервал')


async def get_intervals():
    intervals_kb = InlineKeyboardBuilder()
    intervals_kb.add(InlineKeyboardButton(text="Определённая дата", callback_data=f'intervals_get_date'))
    intervals_kb.add(InlineKeyboardButton(text="Текущая неделя", callback_data=f'intervals_get_week'))
    intervals_kb.add(InlineKeyboardButton(text="Текущий месяц", callback_data=f'intervals_get_month'))
    intervals_kb.add(InlineKeyboardButton(text="Весь период", callback_data=f'intervals_get_all'))
    intervals_kb.add(InlineKeyboardButton(text="<-", callback_data=f'return_admin'))
    return intervals_kb.adjust(2).as_markup()


async def edit_excursions(date_from: str):
    excursions_kb = InlineKeyboardBuilder()
    excs = await get_excursions()
    excs = sorted(excs, key=lambda x: datetime.datetime.strptime(x.date + ' ' + x.time, "%d.%m.%Y %H:%M:%S"))
    for excursion in excs:
        try:
            if datetime.datetime.strptime(date_from, "%d.%m.%Y") == datetime.datetime.strptime(excursion.date,
                                                                                               "%d.%m.%Y"):
                excursions_kb.add(
                    InlineKeyboardButton(text=f"{excursion.date}, {':'.join(str(excursion.time).split(':')[:2])}, "
                                              f"{excursion.contacts.split(', ')[1]}",
                                         callback_data=f'edit_excursion_{excursion.id}_1'))
        except ValueError as exception:
            print(exception)
    excursions_kb.add(InlineKeyboardButton(text="<-", callback_data=f'to_intervals'))
    return excursions_kb.adjust(1).as_markup()


async def edit_properties(excursion_id: int, choice_type: int):
    properties_kb = InlineKeyboardBuilder()
    properties = ['Дата', 'Время', 'Количество человек', 'Маршрут', 'Стоимость', 'Контакты', 'Доп. Информация', 'Гид',
                  'Питание', "Мастер-Класс", "Университет"]
    properties_callback = ['date', 'time', 'people', 'fromplace', 'money', 'contacts', 'additionalinfo', 'guide', 'eat',
                           "mk", "university"]

    for i in range(len(properties)):
        properties_kb.add(InlineKeyboardButton(text=f"{properties[i]}",
                                               callback_data=f'edit_properties_{excursion_id}_{properties_callback[i]}_{choice_type}'))

    properties_kb.add(InlineKeyboardButton(text='Завершить', callback_data=f'finish_{excursion_id}'))
    properties_kb.add(InlineKeyboardButton(text="Удалить", callback_data=f"remove_confirmation_{excursion_id}"))
    if choice_type == 0:
        properties_kb.add(InlineKeyboardButton(text="<-", callback_data=f'to_intervals'))
    elif choice_type == 1:
        properties_kb.add(InlineKeyboardButton(text="<-", callback_data=f'intervals_get_date'))
    elif choice_type == 2:
        properties_kb.add(InlineKeyboardButton(text="<-", callback_data=f'intervals_get_week'))
    elif choice_type == 3:
        properties_kb.add(InlineKeyboardButton(text="<-", callback_data=f'intervals_get_month'))
    elif choice_type == 4:
        properties_kb.add(InlineKeyboardButton(text="<-", callback_data=f'intervals_get_all'))

    return properties_kb.adjust(2).as_markup()


async def finish_excursion(excursion_id: int):
    excursions_kb = InlineKeyboardBuilder()

    excursions_kb.add(InlineKeyboardButton(text=f"{'Завершить'}", callback_data=f'finish_{excursion_id}'))
    excursions_kb.add(InlineKeyboardButton(text=f"{'Вернуться'}", callback_data=f'return_home'))
    excursions_kb.add(InlineKeyboardButton(
        text=f"{'Связаться с менеджером'}",
        url='https://t.me/gotoinno',
        callback_data=f'return_home'))

    return excursions_kb.adjust(2).as_markup()


async def user_excursions(telegram_id: int):
    excursions_kb = InlineKeyboardBuilder()
    excs = await get_user_excursions(telegram_id)
    excs = sorted(excs, key=lambda x: datetime.datetime.strptime(x.date + ' ' + x.time, "%d.%m.%Y %H:%M:%S"))
    for excursion in excs:
        excursions_kb.add(
            InlineKeyboardButton(text=f"{excursion.date}, {':'.join(str(excursion.time).split(':')[:2])}, "
                                      f"{excursion.contacts.split(', ')[1]}",
                                 callback_data=f'user_excursion_{excursion.id}'))
    excursions_kb.add(InlineKeyboardButton(text="<-", callback_data=f'return_home'))
    return excursions_kb.adjust(1).as_markup()


async def get_unfinished():
    excursions_kb = InlineKeyboardBuilder()
    excs = await get_excursions()
    excs = sorted(excs, key=lambda x: datetime.datetime.strptime(x.date + ' ' + x.time, "%d.%m.%Y %H:%M:%S"))
    date = '.'.join(str(datetime.datetime.now().date()).split('-')[::-1])
    for excursion in excs:
        if (excursion.guide is None or len(excursion.guide.split(', ')) < (
                (
                        excursion.people_free + excursion.people_discount + excursion.people_full - 1) // 23) + 1) and compare_dates(
                        excursion.date, date):
            excursions_kb.add(
                InlineKeyboardButton(text=f"{excursion.date}, {':'.join(str(excursion.time).split(':')[:2])}, "
                                          f"{excursion.contacts.split(', ')[1]}",
                                     callback_data=f'appoint_excursion_{excursion.id}'))
    excursions_kb.add(InlineKeyboardButton(text="<-", callback_data=f'return_admin'))
    return excursions_kb.adjust(1).as_markup()


async def week_excursions():
    excursions_kb = InlineKeyboardBuilder()
    excs = await get_week_excursions()
    excs = sorted(excs, key=lambda x: datetime.datetime.strptime(x.date + ' ' + x.time, "%d.%m.%Y %H:%M:%S"))
    for excursion in excs:
        excursions_kb.add(
            InlineKeyboardButton(text=f"{excursion.date}, {':'.join(str(excursion.time).split(':')[:2])}, "
                                      f"{excursion.contacts.split(', ')[1]}",
                                 callback_data=f'edit_excursion_{excursion.id}_2'))
    excursions_kb.add(InlineKeyboardButton(text="<-", callback_data=f'to_intervals'))
    return excursions_kb.adjust(1).as_markup()


async def month_excursions():
    excursions_kb = InlineKeyboardBuilder()
    excs = await get_month_excursions()
    excs = sorted(excs, key=lambda x: datetime.datetime.strptime(x.date + ' ' + x.time, "%d.%m.%Y %H:%M:%S"))
    for excursion in excs:
        excursions_kb.add(
            InlineKeyboardButton(text=f"{excursion.date}, {':'.join(str(excursion.time).split(':')[:2])}, "
                                      f"{excursion.contacts.split(', ')[1]}",
                                 callback_data=f'edit_excursion_{excursion.id}_3'))
    excursions_kb.add(InlineKeyboardButton(text="<-", callback_data=f'to_intervals'))
    return excursions_kb.adjust(1).as_markup()


async def all_excursions():
    excursions_kb = InlineKeyboardBuilder()
    excs = await get_excursions()
    excs = sorted(excs, key=lambda x: datetime.datetime.strptime(x.date + ' ' + x.time, "%d.%m.%Y %H:%M:%S"))
    for excursion in excs:
        excursions_kb.add(
            InlineKeyboardButton(text=f"{excursion.date}, {':'.join(str(excursion.time).split(':')[:2])}, "
                                      f"{excursion.contacts.split(', ')[1]}",
                                 callback_data=f'edit_excursion_{excursion.id}_4'))
    excursions_kb.add(InlineKeyboardButton(text="<-", callback_data=f'to_intervals'))
    return excursions_kb.adjust(2).as_markup()


async def appointed_guides(excursion_id: int, search_type: int):
    guides_kb = InlineKeyboardBuilder()
    guides = await get_guide_list(excursion_id)

    if guides:
        for guide_id in guides:
            user = await get_user_by_id(guide_id)
            guides_kb.add(InlineKeyboardButton(text=f"{user.name}",
                                               callback_data=f'appoint_excursion_{excursion_id}_{user.id}'))

    guides_kb.add(InlineKeyboardButton(text="<-", callback_data=f'edit_excursion_{excursion_id}_{search_type}'))
    return guides_kb.adjust(1).as_markup()


async def free_guides(excursion_id: int, disappoint_guide_id=-1):
    guides_kb = InlineKeyboardBuilder()
    guides = await get_users()
    for guide in guides:
        temp = await get_user(guide)
        schedule = await get_timetable(temp.id)
        excursion = await get_excursion(excursion_id)

        if await time_intersecting(excursion.date, excursion.time, temp.id):
            continue
        else:
            if await get_guide_list(excursion_id):
                if temp.id in await get_guide_list(excursion_id):
                    continue

        days_en = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        try:
            time = getattr(schedule, days_en[datetime.datetime.strptime(excursion.date, "%d.%m.%Y").weekday()]).rstrip(' ').split("; ")
        except Exception:
            logging.error(f'{excursion_id}: {temp.id}. {schedule}')
        if time is not None:
            if time[0] == '+' or time[0] == '+ ' or time[0] == ' +':
                guides_kb.add(InlineKeyboardButton(text=f"{temp.name}",
                                                   callback_data=f'2_appoint_excursion_{temp.id}_{disappoint_guide_id}_{excursion_id}'))
            elif time[0] == '-' or time[0] == '?' or time[0] == ' -' or time[0] == ' ?' or time[0] == '- ' or time[0] == '? ':
                continue
            else:
                for time_interval in time:
                    start, end = time_interval.split('-')

                    excursion_time2 = (
                            datetime.datetime.strptime(excursion.time, "%H:%M:%S") + datetime.timedelta(hours=1,
                                                                                                        minutes=30)).strftime(
                        "%H:%M:%S")
                    if compare_time(excursion.time, start) and compare_time(end, excursion_time2):
                        guides_kb.add(InlineKeyboardButton(text=f"{temp.name}",
                                                           callback_data=f'2_appoint_excursion_{temp.id}_{disappoint_guide_id}_{excursion_id}'))
                        break

    guides_kb.add(InlineKeyboardButton(text="<-", callback_data=f'free_list'))
    return guides_kb.adjust(2).as_markup()


async def timetables_choice():
    timetable_kb = InlineKeyboardBuilder()
    guides = await get_users()
    for guide in guides:
        temp = await get_user(guide)
        timetable_kb.add(InlineKeyboardButton(text=f"{temp.name}",
                                              callback_data=f'timetable_{temp.id}'))
    timetable_kb.add(InlineKeyboardButton(text="<-", callback_data=f'return_admin'))
    return timetable_kb.adjust(2).as_markup()


def remove_confirm(excursion_id: int):
    confirmation_kb = InlineKeyboardBuilder()
    confirmation_kb.add(InlineKeyboardButton(text="Подтвердить", callback_data=f'remove_excursion_{excursion_id}'))
    confirmation_kb.add(InlineKeyboardButton(text="Отменить", callback_data=f'return_home'))

    return confirmation_kb.adjust(2).as_markup()


def people_types(excursion_id: int):
    type_kb = InlineKeyboardBuilder()
    type_kb.add(InlineKeyboardButton(text="Бесплатно", callback_data=f'people_edit_{excursion_id}_free'))
    type_kb.add(InlineKeyboardButton(text="Льготная стоимость", callback_data=f'people_edit_{excursion_id}_discount'))
    type_kb.add(InlineKeyboardButton(text="Полная стоимость", callback_data=f'people_edit_{excursion_id}_full'))

    return type_kb.adjust(1).as_markup()


def food_types(excursion_id: int, complex_number: int):
    type_kb = InlineKeyboardBuilder()
    type_kb.add(InlineKeyboardButton(text="Стандарт",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_1'))
    type_kb.add(InlineKeyboardButton(text="Комплекс 1 (за 450)",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_2'))
    type_kb.add(InlineKeyboardButton(text="Комплекс 2 (за 450)",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_3'))
    type_kb.add(InlineKeyboardButton(text="Халяль",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_4'))
    type_kb.add(InlineKeyboardButton(text="Комплекс в технопарке",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_5'))
    type_kb.add(InlineKeyboardButton(text="Не нужно",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_7'))
    type_kb.add(InlineKeyboardButton(text="Другое",
                                     callback_data=f'food2_edit_{excursion_id}_{complex_number}_6'))

    return type_kb.adjust(1).as_markup()


def set_complex_number(excursion_id: int):
    type_kb = InlineKeyboardBuilder()
    type_kb.add(InlineKeyboardButton(text="Изменить первый комплекс", callback_data=f'food1_edit_{excursion_id}_1'))
    type_kb.add(InlineKeyboardButton(text="Изменить второй комплекс", callback_data=f'food1_edit_{excursion_id}_2'))

    return type_kb.adjust(1).as_markup()


def accept(excursion_id: int):
    type_kb = InlineKeyboardBuilder()
    type_kb.add(InlineKeyboardButton(text="Принять", callback_data=f'accept_excursion_{excursion_id}'))
    type_kb.add(InlineKeyboardButton(text="Отказаться", callback_data=f'decline_excursion_{excursion_id}'))

    return type_kb.adjust(2).as_markup()
