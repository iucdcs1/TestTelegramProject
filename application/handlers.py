import datetime
import datetime as dt

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import application.keyboards as kb
from application.FSM import Form
from application.database.requests import get_user, get_user_statistics, is_admin, reload_excursions, get_excursion, \
    remove_excursion, get_admins, get_user_by_id, add_guide, add_timetable, get_timetable, get_food, change_date, \
    change_time, change_people, change_from_place, change_university, change_contacts, change_money, change_eat, \
    change_mk, change_additional_info, get_guide_list, remove_guide, get_report, add_user
from application.filters import UnknownCommandFilter, AdminCommandFilter
from application.utilities.tools import check_timetable

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    check_result = await get_user(message.from_user.id)
    if check_result:
        if await is_admin(message.from_user.id):
            await message.answer(f"{message.from_user.first_name.upper()}, добро пожаловать в бота-помощника!",
                                 reply_markup=kb.main_admin)
        else:
            await message.answer(f"{message.from_user.first_name.upper()}, добро пожаловать в бота-помощника!",
                                 reply_markup=kb.main)
    else:
        await message.answer("К сожалению, Вас нет в whitelist`е бота.\n"
                             "Если у Вас должен быть доступ - пожалуйста, напишите @NPggL")


@router.message(F.text == 'Профиль')
async def profile(message: Message):
    statistic = await get_user_statistics(message.from_user.id)
    start_date = statistic.start_date
    dt.date.strftime(start_date, "%Y-%m-%d")
    await message.answer('<b>Профиль</b>\n'
                         f'Количество проведённых экскурсий: <b>'
                         f'{int(statistic.amount_groups) + int(statistic.amount_individuals)}</b>\n'
                         f'Одиночных: <b>{int(statistic.amount_individuals)}</b>\n'
                         f'Групповых: <b>{int(statistic.amount_groups)}</b>\n'
                         f'А гидом Вы работаете уже <b>{(dt.date.today() - start_date).days}</b> дней!\n')


@router.message(AdminCommandFilter(), F.text == 'Главная')
async def home_page(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Возвращаю на главную страницу', reply_markup=kb.main_admin)


@router.message(F.text == 'Главная')
async def home_page(message: Message):
    await message.answer('Возвращаю на главную страницу', reply_markup=kb.main)


@router.message(F.text == 'Экскурсии')
async def home_page(message: Message):
    await message.answer('Ваши запланированные экскурсии:', reply_markup=await kb.user_excursions(message.from_user.id))


@router.callback_query(F.data.startswith('user_excursion_'))
async def user_excursion_selected(callback: CallbackQuery):
    excursion_id = int(callback.data.split('_')[2])
    excursion_info = await get_excursion(excursion_id)
    guide_id = (await get_user(callback.from_user.id)).id

    if await get_guide_list(excursion_id) is not None:
        guides = [(await get_user_by_id(int(idx))) for idx in await get_guide_list(excursion_id)]
    else:
        guides = []
    message = f"Информация по выбранной экскурсии ({excursion_id}):\n" \
              f"Время: {excursion_info.date}, {':'.join(str(excursion_info.time).split(':')[:2])}\n" \
              f"Напарники: {', '.join([x.name for x in guides if x.name != (await get_user_by_id(guide_id)).name]) if len(guides) > 1 else 'Отсутствуют'}\n"
    message += f"Количество человек: {excursion_info.people}\n" \
               f"Старт: {excursion_info.from_place}\n" \
               f"Университет: {'+' if excursion_info.university == 1 else '-'}\n" \
               f"Контакт: {excursion_info.contacts}\n" \
               f"МК: {excursion_info.mk}\n" \
               f"Питание: {(await get_food(excursion_info.eat)).place if excursion_info.eat != 0 else 'Нет'}\n" \
               f"Доп. Информация: {excursion_info.additional_info if excursion_info.additional_info != '-' else 'Отсутствует'}"

    await callback.message.answer(message, reply_markup=await kb.finish_excursion(excursion_id))


@router.callback_query(F.data.startswith('finish_'))
async def finish_selected_excursion(callback: CallbackQuery):
    from run import notify_user

    excursion_id = int(callback.data.split('_')[1])
    exc = await get_excursion(excursion_id)

    print(datetime.datetime.now(), datetime.datetime.strptime(exc.date + " " + exc.time, "%d.%m.%Y %H:%M:%S"),
          datetime.datetime.now() + datetime.timedelta(hours=5))
    if datetime.datetime.strptime(exc.date + " " + exc.time, "%d.%m.%Y %H:%M:%S") + datetime.timedelta(hours=1,
                                                                                                       minutes=30) <= datetime.datetime.now():

        guides = [(await get_user_by_id(int(idx))) for idx in await get_guide_list(excursion_id)]

        await remove_excursion(excursion_id, True)

        for guide in guides:
            if guide.telegram_id == callback.from_user.id:
                continue
            await notify_user(guide.telegram_id,
                              f"Экскурсия на {'.'.join(str(exc.time).split(':')[:2])} завершена. Спасибо за работу =)")

        if await is_admin(callback.message.from_user.id):
            await callback.message.answer(f"Экскурсия завершена. Спасибо за работу =)", reply_markup=kb.main_admin)
        else:
            await callback.message.answer(f"Экскурсия завершена. Спасибо за работу =)", reply_markup=kb.main)

        for admin in await get_admins():
            message = f"Экскурсия на {'.'.join(str(exc.time).split(':')[:2])} завершена! (ID={exc.id})\n" \
                      f"Гиды: {', '.join([x.name for x in guides])}\n" \
                      f"Количество человек: {exc.people}\n" \
                      f"Оплата: {exc.money}"
            await notify_user(admin.telegram_id, message)
    else:
        if await is_admin(callback.from_user.id):
            await callback.message.answer(f"Вы не можете завершить экскурсию в данный момент :(\n"
                                          f"Используйте вкладку 'изменение экскурсий' при необходимости!",
                                          reply_markup=kb.main_admin)
        else:
            await callback.message.answer(f"Вы не можете завершить экскурсию в данный момент :(\n"
                                          f"Если возникла какая-то проблема - свяжитесь с менеджером!",
                                          reply_markup=kb.main)


@router.message(AdminCommandFilter(), F.text == 'Админ-панель')
async def admin_panel(message: Message):
    await message.answer('Открыта панель администрирования', reply_markup=kb.admin_panel)


@router.message(AdminCommandFilter(), F.text == 'Изменение экскурсий')
async def edit_excursion(message: Message, state: FSMContext):
    await state.set_state(Form.excursion_choice_date_from)
    await message.answer('Дата экскурсии: (DD.MM.YYYY)', reply_markup=kb.week_panel)


@router.message(AdminCommandFilter(), Form.excursion_choice_date_from, F.text == 'Текущая неделя')
async def current_week(message: Message, state: FSMContext):
    await message.answer('Экскурсии текущей недели:', reply_markup=await kb.week_excursions())
    await message.answer_dice(reply_markup=kb.only_back)
    await state.clear()


@router.message(AdminCommandFilter(), Form.excursion_edit_property)
async def edit_chosen_property(message: Message, state: FSMContext):
    import re

    data = await state.get_data()
    excursion_id = data['excursion_id']
    excursion_property = data['excursion_property']

    if excursion_property == "date":
        pattern = re.compile("\d{2}.\d{2}.\d{4}")
        if re.match(pattern, message.text):
            await change_date(excursion_id, message.text)
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат", reply_markup=kb.admin_panel)
    elif excursion_property == "time":
        pattern = re.compile("\d{2}:\d{2}")
        if re.match(pattern, message.text):
            await change_time(excursion_id, message.text)
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат", reply_markup=kb.admin_panel)
    elif excursion_property == "people":
        pattern = re.compile('\d{1,2}')
        if re.match(pattern, message.text):
            await change_people(excursion_id, message.text)
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат", reply_markup=kb.admin_panel)
    elif excursion_property == "fromplace":
        if message.text in ["Университет", "ОЭЗ", "Артспейс"]:
            await change_from_place(excursion_id, message.text)
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат, варианты: Университет, ОЭЗ, Артспейс", reply_markup=kb.admin_panel)
    elif excursion_property == "contacts":
        pattern = re.compile('^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$')
        if re.match(pattern, message.text.split(', ')[0]) and len(message.text.split(', ')) == 2:
            await change_contacts(excursion_id, message.text)
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат, пример: +71234567890, Имя", reply_markup=kb.admin_panel)
    elif excursion_property == "money":
        pattern = re.compile('[0-9]+')
        if re.match(pattern, message.text):
            await change_money(excursion_id, int(message.text))
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат", reply_markup=kb.admin_panel)
    elif excursion_property == "eat":
        if message.text in ["0", "1", "2", "3"]:
            await change_eat(excursion_id, int(message.text))
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer("Неверный формат, варианты: (0, 1, 2, 3)", reply_markup=kb.admin_panel)
    elif excursion_property == "mk":
        if message.text in ["Чат-бот", "Графический дизайн", "Интернет вещей", "Робототехника", "Оригаметрия", "ИЗО",
                            "Нет"]:
            await change_mk(excursion_id, message.text)
            await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)
        else:
            await message.answer(
                "Неверный формат, варианты: (Чат-бот, Графический дизайн, Интернет вещей, Робототехника, Оригаметрия, ИЗО, Нет)",
                reply_markup=kb.admin_panel)
    elif excursion_property == "additionalinfo":
        await change_additional_info(excursion_id, message.text)
        await message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)

    await state.clear()


@router.message(AdminCommandFilter(), Form.excursion_choice_date_from)
async def getting_excursion(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Результат:\n", reply_markup=await kb.edit_excursions(message.text))


@router.message(Form.timetable)
async def save_timetable(message: Message, state: FSMContext):
    await state.clear()

    if check_timetable(message.text):
        await add_timetable((await get_user(message.from_user.id)).id, message.text)
        if await is_admin(message.from_user.id):
            await message.answer("Расписание успешно обновлено!", reply_markup=kb.main_admin)
        else:
            await message.answer("Расписание успешно обновлено!", reply_markup=kb.main)
    else:
        if await is_admin(message.from_user.id):
            await message.answer("Неверный формат расписания. Пожалуйста, используйте пример в качестве шаблона!",
                                 reply_markup=kb.main_admin)
        else:
            await message.answer("Неверный формат расписания. Пожалуйста, используйте пример в качестве шаблона!",
                                 reply_markup=kb.main)


@router.message(F.text == 'Админ-панель')
async def refused_admin_command(message: Message):
    await message.answer('Неизвестная команда', reply_markup=kb.main)


@router.message(AdminCommandFilter(), F.text == 'Отчёт')
async def choose_report_interval(message: Message):
    await message.answer('Выберите временной интервал для отчёта', reply_markup=kb.report_intervals)


@router.message(AdminCommandFilter(), F.text == 'Отчёт за день')
async def daily_report(message: Message):
    await message.answer('Отчёт за день:', reply_markup=kb.main_admin)
    await message.answer(str(await get_report(datetime.datetime.today().strftime("%d.%m.%Y"),
                                              datetime.datetime.today().strftime("%d.%m.%Y"))))


@router.message(AdminCommandFilter(), F.text == 'Отчёт за неделю')
async def weekly_report(message: Message):
    await message.answer('Отчёт за неделю:', reply_markup=kb.main_admin)
    today = datetime.datetime.today()
    await message.answer(str(await get_report((today - datetime.timedelta(days=today.isoweekday())).strftime("%d.%m.%Y"),
                                              (today + datetime.timedelta(days=(7 - today.isoweekday()))).strftime("%d.%m.%Y"))))


@router.message(AdminCommandFilter(), F.text == 'Отчёт за месяц')
async def monthly_report(message: Message):
    await message.answer('Отчёт за месяц:', reply_markup=kb.main_admin)
    last_day = datetime.datetime.today().strftime("01.%m.%Y").split('.')
    last_day[1] = str(int(last_day[1]) + 1)
    last_day = int(
        (datetime.datetime.strptime('.'.join(last_day), "%d.%m.%Y") - datetime.timedelta(days=1)).strftime("%d"))
    await message.answer(str(await get_report(datetime.datetime.today().strftime("01.%m.%Y"),
                                              datetime.datetime.today().strftime(f"{last_day}.%m.%Y"))))


@router.message(AdminCommandFilter(), F.text == 'Общий отчёт')
async def overall_report(message: Message):
    await message.answer('Отчёт за всё время:', reply_markup=kb.main_admin)
    await message.answer(str(await get_report('01.01.1970', '01.01.2100')))


@router.message(AdminCommandFilter(), F.text == 'Выгрузка экскурсий')
async def download_excursions(message: Message):
    await message.answer('Началась выгрузка... Пожалуйста, подождите')
    await reload_excursions()
    await message.answer('Выгрузка завершена', reply_markup=kb.admin_panel)


@router.message(AdminCommandFilter(), F.text == 'Назначение')
async def download_excursions(message: Message):
    await message.answer('Список экскурсий требующих назначение:', reply_markup=await kb.get_unfinished())


@router.message(F.text == 'Расписание')
async def set_timetable(message: Message, state: FSMContext):
    await state.set_state(Form.timetable)
    await message.answer('Введите ваше расписание на текущую неделю в следующем формате (пример):')
    await message.answer(f'ПН: -\n'
                         f'ВТ: +\n'
                         f'СР: 09.00-11:00; 12:00-13:30; 15:00-17:00\n'
                         f'ЧТ: 08:30-11:30; 13:00-14:45\n'
                         f'ПТ: +\n'
                         f'СБ: 08:00-12:00; 14:00-16:30\n'
                         f'ВС: -')
    await message.answer("+ значит, что вы полностью свободны в этот день.\n"
                         "- значит, что вы не сможете работать в этот день.\n"
                         "? значит, что вы пока не знаете о режиме работы в этот день\n"
                         "Просьба в точности соблюдать формат!")


@router.message(F.text == 'Просмотреть расписание')
async def watch_timetable(message: Message):
    await message.answer('Выберите, чьё расписание посмотреть', reply_markup=await kb.timetables_choice())


@router.callback_query(AdminCommandFilter(), F.data.startswith('disappoint'))
async def disappoint_guide(callback: CallbackQuery):
    excursion_id = int(callback.data.split('_')[2])
    await callback.message.answer('Выберите, какого гида переназначить:',
                                  reply_markup=await kb.appointed_guides(excursion_id))


@router.callback_query(AdminCommandFilter(), F.data.startswith('appoint'))
async def appoint_excursion(callback: CallbackQuery):
    excursion_id = int(callback.data.split('_')[2])
    if len(callback.data.split('_')) == 4:
        disappoint_guide_id = int(callback.data.split('_')[3])
        await callback.message.answer('Выберите гида для назначения:',
                                      reply_markup=await kb.free_guides(excursion_id,
                                                                        disappoint_guide_id=disappoint_guide_id))
    else:
        await callback.message.answer('Выберите гида для назначения:',
                                      reply_markup=await kb.free_guides(excursion_id))


@router.callback_query(AdminCommandFilter(), F.data.startswith('2_appoint'))
async def appoint_excursion_final(callback: CallbackQuery):
    from run import notify_user

    excursion_id = int(callback.data.split('_')[5])
    guide_id = int(callback.data.split('_')[3])

    disappoint_guide_id = int(callback.data.split('_')[4])
    if disappoint_guide_id != -1:
        await remove_guide(excursion_id, disappoint_guide_id)

    await add_guide(excursion_id, guide_id)
    await callback.message.answer("Гид был назначен!", reply_markup=kb.admin_panel)

    excursion_info = await get_excursion(excursion_id)

    guides = [(await get_user_by_id(int(idx))) for idx in await get_guide_list(excursion_id)]

    message = f"Вам назначена экскурсия ({excursion_id}):\n" \
              f"Время: {excursion_info.date}, {':'.join(str(excursion_info.time).split(':')[:2])}\n" \
              f"Количество человек: {excursion_info.people}\n" \
              f"Место: {excursion_info.from_place}\n" \
              f"Университет: {'+' if excursion_info.university == 1 else '-'}\n" \
              f"Контакт: {excursion_info.contacts}\n" \
              f"Напарники: {', '.join([x.name for x in guides if x.name != (await get_user_by_id(guide_id)).name])}\n" \
              f"Доп. Информация: {excursion_info.additional_info if excursion_info.additional_info != '-' else 'отсутствует'}"

    telegram_id = (await get_user_by_id(guide_id)).telegram_id
    await notify_user(telegram_id, message)


@router.callback_query(F.data == 'return_home')
async def return_to_panel(callback: CallbackQuery):
    if await is_admin(callback.from_user.id):
        await callback.message.answer('Открыта главная страница администратора', reply_markup=kb.main_admin)
    else:
        await callback.message.answer('Открыта главная страница', reply_markup=kb.main)


@router.callback_query(AdminCommandFilter(), F.data.startswith('timetable_'))
async def draw_timetable(callback: CallbackQuery):
    guide_id = int(callback.data.split('_')[1])
    timetable = await get_timetable(guide_id)
    message = f"ПН: {timetable.mon if timetable.mon else '?'}\n" + "-" * 40 + "\n" \
                                                                              f"ВТ: {timetable.tue if timetable.tue else '?'}\n" + "-" * 40 + "\n" \
                                                                                                                                              f"СР: {timetable.wed if timetable.wed else '?'}\n" + "-" * 40 + "\n" \
                                                                                                                                                                                                              f"ЧТ: {timetable.thu if timetable.thu else '?'}\n" + "-" * 40 + "\n" \
                                                                                                                                                                                                                                                                              f"ПТ: {timetable.fri if timetable.fri else '?'}\n" + "-" * 40 + "\n" \
                                                                                                                                                                                                                                                                                                                                              f"СБ: {timetable.sat if timetable.sat else '?'}\n" + "-" * 40 + "\n" \
                                                                                                                                                                                                                                                                                                                                                                                                              f"ВС: {timetable.sun if timetable.sun else '?'}\n"

    message = message.replace(' -', ' Не работает').replace(' +', ' Любое время') \
        .replace(' ?', ' Неизвестно').replace('; ', ' | ')

    await callback.message.answer(message, reply_markup=kb.main_admin)


@router.message(AdminCommandFilter(), F.text.startswith("Добавить пользователя"))
async def add_user_guide(message: Message):
    data = message.text.split(' ')
    telegram_id, name, admin = int(data[2]), data[3], data[4]
    if admin == '1':
        admin = True
    else:
        admin = False
    print('\n' * 10, data)
    await add_user(telegram_id, name, admin)
    await message.answer(f"Пользователь {telegram_id} был добавлен в whitelist!")


@router.callback_query(AdminCommandFilter(), F.data.startswith('edit_excursion_'))
async def excursion_selected(callback: CallbackQuery):
    excursion_id = int(callback.data.split('_')[2])
    excursion_info = await get_excursion(excursion_id)

    if await get_guide_list(excursion_id) is not None:
        guides = [(await get_user_by_id(int(idx))) for idx in await get_guide_list(excursion_id)]
    else:
        guides = []
    message = f"Информация по выбранной экскурсии ({excursion_id}):\n" \
              f"Время: {excursion_info.date}, {':'.join(str(excursion_info.time).split(':')[:2])}\n" \
              f"Гиды: {', '.join([x.name for x in guides]) if guides != [] else 'Отсутствуют'}\n"
    message += f"Количество человек: {excursion_info.people}\n" \
               f"Старт: {excursion_info.from_place}\n" \
               f"Университет: {'+' if excursion_info.university == 1 else '-'}\n" \
               f"Контакт: {excursion_info.contacts}\n" \
               f"МК: {excursion_info.mk}\n" \
               f"Питание: {(await get_food(excursion_info.eat)).place if excursion_info.eat != 0 else 'Нет'}\n" \
               f"Стоимость: {excursion_info.money}\n" \
               f"Доп. Информация: {excursion_info.additional_info if excursion_info.additional_info != '-' else 'Отсутствует'}\n\n" \
               f"Что нужно изменить?"

    await callback.message.answer(message, reply_markup=await kb.edit_properties(excursion_id))


@router.callback_query(AdminCommandFilter(), F.data.startswith('edit_properties_'))
async def excursion_properties_edit(callback: CallbackQuery, state: FSMContext):
    excursion_id = int(callback.data.split('_')[2])
    excursion_property = callback.data.split('_')[3]
    await state.set_state(Form.excursion_edit_property)
    await state.update_data(excursion_id=excursion_id, excursion_property=excursion_property)

    if excursion_property == 'date':
        await callback.message.answer(f'Введите новую дату вместо текущей ({(await get_excursion(excursion_id)).date})',
                                      reply_markup=kb.only_back_properties)
    elif excursion_property == 'time':
        temp = (await get_excursion(excursion_id)).time[:5].replace('.', ':')
        await callback.message.answer(
            f'Введите новое время вместо текущего ({temp})', reply_markup=kb.only_back_properties)
    elif excursion_property == 'people':
        await callback.message.answer(
            f'Введите новое количество гостей вместо текущего ({(await get_excursion(excursion_id)).people})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'fromplace':
        await callback.message.answer(
            f'Введите новое место встречи вместо текущего ({(await get_excursion(excursion_id)).from_place})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'money':
        await callback.message.answer(
            f'Введите новую стоимость вместо текущей ({(await get_excursion(excursion_id)).money})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'contacts':
        await callback.message.answer(
            f'Введите новые контактные данные вместо текущих ({(await get_excursion(excursion_id)).contacts})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'additionalinfo':
        await callback.message.answer(
            f'Введите новую доп. информацию данные вместо текущей ({(await get_excursion(excursion_id)).additional_info})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'guide':
        await state.clear()
        await callback.message.answer(
            f'Выберите какого экскурсовода заменить:',
            reply_markup=await kb.appointed_guides(excursion_id))
    elif excursion_property == 'eat':
        await callback.message.answer(
            f'Введите новое место вместо текущего ({(await get_excursion(excursion_id)).eat})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'mk':
        await callback.message.answer(
            f'Введите новый мастер-класс вместо текущего ({(await get_excursion(excursion_id)).mk})',
            reply_markup=kb.only_back_properties)
    elif excursion_property == 'university':
        await state.clear()
        await change_university(excursion_id)
        await callback.message.answer(f'Изменение внесено!', reply_markup=kb.admin_panel)


@router.message(UnknownCommandFilter([None, "/start", "Профиль",
                                      "Админ-панель", "Главная",
                                      "Изменение экскурсий", "Выгрузка экскурсий",
                                      "Экскурсии", "Текущая неделя", "Назначение",
                                      "Расписание", "Просмотреть расписание",
                                      "Добавить пользователя"]))
async def unknown_command(message: Message):
    await message.answer("Неизвестная команда")