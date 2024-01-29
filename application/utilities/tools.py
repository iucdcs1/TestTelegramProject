import datetime


def compare_dates(date1: str, date2: str) -> bool:
    date1, date2 = list(map(int, date1.split('.'))), list(map(int, date2.split('.')))
    if date1[2] > date2[2]:
        return True
    elif date1[2] == date2[2]:
        if date1[1] > date2[1]:
            return True
        elif date1[1] == date2[1]:
            if date1[0] >= date2[0]:
                return True
            else:
                return False


def compare_time(time1: str, time2: str) -> bool:
    time1, time2 = list(map(int, time1.split(':'))), list(map(int, time2.split(':')))
    if time1[0] > time2[0]:
        return True
    elif time1[0] == time2[0]:
        if time1[1] >= time2[1]:
            return True
        else:
            return False
    else:
        return False


def compare_dates_interval(date_from, date_to, date) -> bool:
    if compare_dates(date, date_from) and compare_dates(date_to, date):
        return True
    return False


async def time_intersecting(exc_date: str, exc_time: str, guide_id: int):
    from application.database.requests import get_user_excursions, get_user_by_id

    excursions = await get_user_excursions((await get_user_by_id(guide_id)).telegram_id)

    for excursion in excursions:
        if excursion.date == exc_date:
            if datetime.datetime.strptime(excursion.time, "%H:%M:%S").time() <= datetime.datetime.strptime(exc_time,
                                                                                                           "%H:%M:%S").time() < (
                    datetime.datetime.strptime(excursion.time, "%H:%M:%S") + datetime.timedelta(hours=1,
                                                                                                minutes=30)).time():
                return True
            if datetime.datetime.strptime(excursion.time, "%H:%M:%S").time() < (
                    datetime.datetime.strptime(exc_time, "%H:%M:%S") + datetime.timedelta(hours=1,
                                                                                          minutes=30)).time() <= (
                    datetime.datetime.strptime(excursion.time, "%H:%M:%S") + datetime.timedelta(hours=1,
                                                                                                minutes=30)).time():
                return True
    return False


def check_timetable(timetable: str) -> bool:
    timetable = timetable.split('\n')
    if len(timetable) != 7:
        print("BAD DAYS NUMBER")
        return False
    else:
        for day in timetable:
            temporary = day.split(": ")
            if len(temporary) != 2:
                print("BAD LENGTH : ")
                return False
            else:
                time_intervals = temporary[1].split("; ")
                if len(time_intervals) == 0:
                    print("NO INTERVALS")
                    return False
                else:
                    for time_interval in time_intervals:
                        if time_interval != "+" and time_interval != "-" and time_interval != "?" and len(
                                time_interval.split("-")) != 2:
                            print("WRONG INTERVAL")
                            return False
                        else:
                            print(time_interval)
                            if time_interval != "+" and time_interval != "-" and time_interval != "?" and len(
                                    time_interval.split("-")) == 2:
                                time_interval = time_interval.split("-")
                                start, end = time_interval[0], time_interval[1]
                                if start.count(':') != 1 or end.count(':') != 1:
                                    print("NO : IN INTERVAL")
                                    return False
                                else:
                                    start = start.replace(':', '')
                                    end = end.replace(':', '')
                                    for alpha, alpha2 in zip(start, end):
                                        if alpha not in [str(i) for i in range(0, 10)] or alpha2 not in [str(i) for i in
                                                                                                         range(0, 10)]:
                                            print("NOT A NUMBER")
                                            return False

    return True


async def notify_guides(excursion_id: int, message: str):
    from application.database.requests import get_guide_list, get_user_by_id
    from run import notify_user

    guide_list = await get_guide_list(excursion_id)

    if guide_list:
        for guide_id in guide_list:
            telegram_id = (await get_user_by_id(int(guide_id))).telegram_id
            await notify_user(telegram_id, message)


async def recommend_appointment():
    from application.database.requests import get_day_excursions, get_users, get_user, get_timetable
    excursions = await get_day_excursions()
    guide_schedules = {}

    guide_ids = [(await get_user(guide_tg)).id for guide_tg in (await get_users())]

    for guide_id in guide_ids:
        guide_schedules[guide_id] = (await get_timetable(guide_id))

    def is_guide_available(guide_schedule_inner, exc):
        days_en = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        time = getattr(guide_schedule_inner, days_en[datetime.datetime.strptime(exc.date, "%d.%m.%Y").weekday()]).split("; ")
        if time is not None:
            if time[0] == "+":
                return True
            elif time[0] in ["-", "?"]:
                return False
            else:
                for time_interval in time:
                    start, end = time_interval.split('-')
                    excursion_time2 = (
                            datetime.datetime.strptime(exc.time, "%H:%M:%S") + datetime.timedelta(hours=1,
                                                                                                  minutes=30)).strftime(
                        "%H:%M:%S")
                    if compare_time(exc.time, start) and compare_time(end, excursion_time2):
                        return True
        return False

    def backtrack_step(excursion_idx, guide_schedules_backtrack: dict, appointment: dict):
            for guide_id_backtrack in guide_ids:
                if is_guide_available(guide_schedules_backtrack[guide_id_backtrack], excursions[excursion_idx]):
                    appointment[excursion_idx].append(guide_id_backtrack)


async def construct_message(excursion_id: int, is_guide=False) -> str:
    from application.database.requests import get_excursion, get_guide_list, get_user_by_id

    excursion_info = await get_excursion(excursion_id)
    if excursion_info.eat1_amount == 0:
        if excursion_info.eat2_amount == 0:
            message_food = "\nОтсутствует"
        else:
            message_food = f'\n{excursion_info.eat2_type}: {excursion_info.eat2_amount} чел.'
    else:
        if excursion_info.eat2_amount == 0:
            message_food = f'\n{excursion_info.eat1_type}: {excursion_info.eat1_amount} чел.'
        else:
            message_food = f'\n{excursion_info.eat1_type}: {excursion_info.eat1_amount} чел.\n{excursion_info.eat2_type}: {excursion_info.eat2_amount} чел.'
    if await get_guide_list(excursion_id) is not None:
        guides = [(await get_user_by_id(int(idx))) for idx in await get_guide_list(excursion_id)]
    else:
        guides = []

    if not is_guide:
        message = f"Информация по выбранной экскурсии ({excursion_id}):\n" \
                  f"Время: {excursion_info.date}, {':'.join(str(excursion_info.time).split(':')[:2])}\n" \
                  f"Гиды: {', '.join([x.name for x in guides]) if guides != [] else 'Отсутствуют'}\n"
        message += f"Количество человек: {excursion_info.people_free + excursion_info.people_discount + excursion_info.people_full}\n" \
                   f"Старт: {excursion_info.from_place}\n" \
                   f"Университет: {'+' if excursion_info.university == 1 else '-'}\n" \
                   f"Контакт: {excursion_info.contacts}\n" \
                   f"МК: {excursion_info.mk}\n" \
                   f"------------------------------\nПитание: {message_food}\n------------------------------\n" \
                   f"Стоимость: {excursion_info.money}\n" \
                   f"Доп. Информация: {excursion_info.additional_info if excursion_info.additional_info != '-' else 'Отсутствует'}\n"
    else:
        message = f"Информация по выбранной экскурсии ({excursion_id}):\n" \
                  f"Время: {excursion_info.date}, {':'.join(str(excursion_info.time).split(':')[:2])}\n" \
                  f"Гиды: {', '.join([x.name for x in guides]) if guides != [] else 'Отсутствуют'}\n"
        message += f"Количество человек: {excursion_info.people_free + excursion_info.people_discount + excursion_info.people_full}\n" \
                   f"Старт: {excursion_info.from_place}\n" \
                   f"Университет: {'+' if excursion_info.university == 1 else '-'}\n" \
                   f"Контакт: {excursion_info.contacts}\n" \
                   f"МК: {excursion_info.mk}\n" \
                   f"------------------------------\nПитание: {message_food}\n------------------------------\n" \
                   f"Доп. Информация: {excursion_info.additional_info if excursion_info.additional_info != '-' else 'Отсутствует'}\n"

    return message

