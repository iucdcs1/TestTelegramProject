import datetime as dt
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from application.api.google_apis import remove_past_excursions
from application.database.requests import get_users, get_user, get_user_excursions, get_timetable, get_guide_list


async def notify_guides():
    from run import notify_user

    guides = await get_users()
    for guide in guides:
        guide_excursions = await get_user_excursions(guide)
        for excursion in guide_excursions:
            excursion_guides = await get_guide_list(excursion.id)
            if dt.datetime.strptime(excursion.date, "%d.%m.%Y") == dt.datetime.now().date():
                message = f"На сегодня у Вас назначена экскурсия ({excursion.id}):\n" \
                          f"Время: {excursion.date}, {'.'.join(str(excursion.time).split(':')[:2])}\n" \
                          f"Количество человек: {excursion.people}\n" \
                          f"Напарники: {', '.join([x.name for x in excursion_guides if x != (await get_user(guide)).name])}\n" \
                          f"Место: {excursion.from_place if excursion.from_place else 'Университет'}\n" \
                          f"Университет: {'+' if excursion.university == 1 else '-'}\n" \
                          f"Контакт: {excursion.contacts}\n" \
                          f"Доп. Информация: {excursion.additional_info if excursion.additional_info != '-' else 'Отсутствует'}"
                await notify_user(guide, message)


async def notify_excursion():
    from run import notify_user

    guides = await get_users()
    for guide in guides:
        guide_excursions = await get_user_excursions(guide)
        for excursion in guide_excursions:

            excursion_datetime = dt.datetime.strptime(excursion.date + ' ' + excursion.time, "%d.%m.%Y %H:%M:%S")
            current_datetime = dt.datetime.now().replace(microsecond=0)

            if (excursion_datetime - current_datetime) == dt.timedelta(
                    hours=1) and excursion_datetime > current_datetime:
                excursion_guides = await get_guide_list(excursion.id)
                message = f"Напоминание! Менее чем через час у вас запланирована экскурсия ({excursion.id}):\n" \
                          f"Время: {excursion.date}, {'.'.join(str(excursion.time).split(':')[:2])}\n" \
                          f"Количество человек: {excursion.people}\n" \
                          f"Напарники: {', '.join([x.name for x in excursion_guides if x != (await get_user(guide)).name])}\n" \
                          f"Место: {excursion.from_place if excursion.from_place else 'Университет'}\n" \
                          f"Университет: {'+' if excursion.university == 1 else '-'}\n" \
                          f"Контакт: {excursion.contacts}\n" \
                          f"Доп. Информация: {excursion.additional_info if excursion.additional_info != '-' else 'Отсутствует'}"
                await notify_user(guide, message)


async def notify_timetable():
    from run import notify_user

    guides = await get_users()
    for guide in guides:
        timetable = await get_timetable((await get_user(guide)).id)
        days_en = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        message = 'Пожалуйста, заполните своё расписание, воспользовавшись меню бота (кнопка "Расписание")!\n' \
                  'Отсутствующие дни: '

        for day_en, day_ru in zip(days_en, days_ru):
            if not getattr(timetable, day_en):
                message += f'{day_ru}, '
            elif getattr(timetable, day_en) == '?':
                message += f'{day_ru}, '

        if message == 'Пожалуйста, заполните своё расписание, воспользовавшись меню бота (кнопка "Расписание")!\n' \
                      'Отсутствующие дни: ':
            pass
        else:
            message = message[:-2]
            await notify_user(guide, message)


async def setup_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_excursion, "interval", minutes=5,
                      next_run_time=dt.datetime.now() + dt.timedelta(minutes=5 - (dt.datetime.now().minute % 5 + 1),
                                                                     seconds=60 - dt.datetime.now().second))
    scheduler.add_job(notify_guides, "cron", hour="7", minute="00")
    scheduler.add_job(remove_past_excursions, "cron", hour="23", minute="55")
    scheduler.add_job(notify_timetable, "cron", hour="12", minute="00")

    return scheduler
