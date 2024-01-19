import datetime

from application.utilities.tools import compare_dates, compare_dates_interval

from sqlalchemy import select, insert, delete, update

from application.api.google_sheet import get_excursions_from_sheet
from application.database.models import User, Statistic, async_session, Excursion, Schedule, ExcursionReport

from application.python_models import Excursion as Exc, Report


async def get_user(telegram_id: int) -> User:
    async with async_session() as session:
        result = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        return result


async def get_users() -> [str]:
    async with async_session() as session:
        users = await session.scalars(select(User))
        result = []
        for user in users:
            result.append(str(user.telegram_id))
        return result


async def get_users_id() -> [int]:
    async with async_session() as session:
        users = await session.scalars(select(User))
        result = []
        for user in users:
            result.append(str(user.id))
        return result


async def get_user_statistics(telegram_id: int) -> [str]:
    async with async_session() as session:
        temporary_query = select(User.id).where(User.telegram_id == telegram_id)
        result = await session.scalar(select(Statistic).where(Statistic.user_id == temporary_query))
        return result


async def is_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        query_result = await session.scalar(select(User.is_admin).where(User.telegram_id == telegram_id))
        if query_result == 1:
            return True
        else:
            return False


async def get_admins() -> [User]:
    async with async_session() as session:
        query_result = await session.scalars(select(User).where(User.is_admin == 1))
        return query_result


async def get_user_by_id(user_id: int) -> User:
    async with async_session() as session:
        query_result = await session.scalar(select(User).where(User.id == user_id))
        return query_result


async def get_excursions() -> [Excursion]:
    async with async_session() as session:
        resulting = await session.scalars(select(Excursion))
        return resulting


async def get_excursion(excursion_id: int) -> Excursion:
    async with async_session() as session:
        result = await session.scalar(select(Excursion).where(Excursion.id == excursion_id))
        return result


async def get_week_excursions() -> [Excursion]:
    async with async_session() as session:
        date_from = '.'.join(str(datetime.datetime.now().date()).split('-')[::-1])
        date_to = '.'.join(str(datetime.datetime.now().date() + datetime.timedelta(days=7)).split('-')[::-1])
        query = await session.scalars(select(Excursion))
        result = []
        for excursion in query:
            if compare_dates_interval(date_from, date_to, excursion.date) is True:
                result.append(excursion)
        return result


async def get_month_excursions() -> [Excursion]:
    async with async_session() as session:
        date_from = '.'.join(str(datetime.datetime.now().date()).split('-')[::-1])
        date_to = '.'.join(str(datetime.datetime.now().date() + datetime.timedelta(days=30)).split('-')[::-1])
        query = await session.scalars(select(Excursion))
        result = []
        for excursion in query:
            if compare_dates_interval(date_from, date_to, excursion.date) is True:
                result.append(excursion)
        return result


async def get_guide_list(excursion_id: int) -> [str]:
    async with async_session() as session:
        query_result = (await session.scalar(select(Excursion).where(Excursion.id == excursion_id))).guide
        if query_result == '' or query_result is None:
            return None
        else:
            return list(map(int, query_result.split(', ')))


async def get_user_excursions(telegram_id: int) -> [Excursion]:
    user_id = (await get_user(telegram_id)).id
    date = '.'.join(str(datetime.datetime.now().date()).split('-')[::-1])
    query_result = []
    res1 = []
    async with async_session() as session:
        query_result = await session.scalars(select(Excursion))
        for exc in query_result:
            if await get_guide_list(exc.id):
                if user_id in (await get_guide_list(exc.id)):
                    res1.append(exc)

    result = []
    for excursion in res1:
        if compare_dates(excursion.date, date):
            result.append(excursion)

    return result


async def reload_excursions() -> None:
    excursions = await get_excursions_from_sheet()
    async with async_session() as session:
        for exc in excursions:
            query_result = await session.scalar(select(Excursion)
                                                .where(Excursion.date == exc.date)
                                                .where(Excursion.time == exc.time)
                                                .where(Excursion.people_discount == exc.people_discount)
                                                .where(Excursion.people_full == exc.people_full)
                                                .where(Excursion.contacts == exc.contacts))
            if not query_result:
                query = insert(Excursion).values(
                    date=exc.date,
                    time=exc.time,
                    people_full=exc.people_full,
                    people_discount=exc.people_discount,
                    people_free=exc.people_free,
                    contacts=exc.contacts,
                    additional_info=exc.additional_info,
                    eat1_type=exc.eat1_type,
                    eat1_amount=exc.eat1_amount,
                    eat2_type=exc.eat2_type,
                    eat2_amount=exc.eat2_amount,
                    mk=exc.mk,
                    from_place=exc.from_place,
                    university=exc.university,
                    money=exc.money,
                    is_group=exc.is_group
                )
                await session.execute(query)
                await session.commit()


async def remove_excursion(excursion_id: int, finished: bool) -> None:
    async with async_session() as session:
        query = (delete(Excursion).where(Excursion.id == excursion_id))
        if finished:
            excursion_info = await get_excursion(excursion_id)
            guides = await get_guide_list(excursion_id)
            if guides is None:
                pass
            else:
                for guide in guides:
                    if (excursion_info.people_full + excursion_info.people_free + excursion_info.people_discount) < 6:
                        statement = (update(Statistic).values(amount_individuals=Statistic.amount_individuals + 1).where(
                            Statistic.user_id == int(guide)))
                    else:
                        statement = (update(Statistic).values(amount_groups=Statistic.amount_groups + 1).where(
                            Statistic.user_id == int(guide)))
                    await session.execute(statement)
            await session.execute((insert(ExcursionReport).values(
                time=excursion_info.time,
                date=excursion_info.date,
                people_free=excursion_info.people_free,
                people_discount=excursion_info.people_discount,
                people_full=excursion_info.people_full,
                university=excursion_info.university,
                contacts=excursion_info.contacts,
                money=excursion_info.money,
                eat1_type=excursion_info.eat1_type,
                eat1_amount=excursion_info.eat1_amount,
                eat2_type=excursion_info.eat2_type,
                eat2_amount=excursion_info.eat2_amount,
                mk=excursion_info.mk,
                transfer=excursion_info.transfer,
                additional_info=excursion_info.additional_info,
                is_group=excursion_info.is_group,
                finished=finished
            )))
        await session.execute(query)
        await session.commit()


async def add_excursion(exc: Exc) -> bool:
    async with async_session() as session:
        query_result = await session.scalar(select(Excursion)
                                            .where(Excursion.date == exc.date)
                                            .where(Excursion.time == exc.time)
                                            .where(Excursion.people_discount == exc.people_discount)
                                            .where(Excursion.people_full == exc.people_full)
                                            .where(Excursion.contacts == exc.contacts))
        if not query_result:
            query = insert(Excursion).values(
                date=exc.date,
                time=exc.time,
                people_full=exc.people_full,
                people_discount=exc.people_discount,
                people_free=exc.people_free,
                contacts=exc.contacts,
                additional_info=exc.additional_info,
                eat1_type=exc.eat1_type,
                eat1_amount=exc.eat1_amount,
                eat2_type=exc.eat2_type,
                eat2_amount=exc.eat2_amount,
                mk=exc.mk,
                from_place=exc.from_place,
                university=exc.university,
                money=exc.money,
                is_group=exc.is_group
            )
            await session.execute(query)
            await session.commit()
            return True
        else:
            return False


async def add_guide(excursion_id: int, guide_id: int):
    async with async_session() as session:
        temp = await get_guide_list(excursion_id)
        if not temp:
            temp = str(guide_id)
        else:
            temp.append(str(guide_id))
            temp = ', '.join([str(x) for x in temp])
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(guide=temp))
        await session.commit()


async def remove_guide(excursion_id: int, guide_id: int):
    from run import notify_user
    async with async_session() as session:
        temp = await get_guide_list(excursion_id)
        result = ''
        print(temp, "\n" * 10)
        if len(temp) == 1:
            pass
        else:
            for guide in temp:
                if guide != guide_id:
                    if result == '':
                        result += guide
                    else:
                        result += ', ' + guide

        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(guide=result))
        await session.commit()
        await notify_user((await get_user_by_id(guide_id)).telegram_id, f"Экскурсия на {':'.join((await get_excursion(excursion_id)).time.split(':')[:2])} была отменена!")


async def add_timetable(guide_id: int, tt: str):
    async with async_session() as session:
        tt = tt.split('\n')

        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(mon=tt[0].split(': ')[1]))
        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(tue=tt[1].split(': ')[1]))
        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(wed=tt[2].split(': ')[1]))
        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(thu=tt[3].split(': ')[1]))
        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(fri=tt[4].split(': ')[1]))
        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(sat=tt[5].split(': ')[1]))
        await session.execute(update(Schedule).where(Schedule.user_id == guide_id).values(sun=tt[6].split(': ')[1]))

        await session.commit()


async def get_timetable(guide_id: int) -> Schedule:
    async with async_session() as session:
        result = await session.scalar(select(Schedule).where(Schedule.user_id == guide_id))
        return result


'''
async def get_food(food_id: int) -> Food:
    async with async_session() as session:
        result = await session.scalar(select(Food).where(Food.id == food_id))
        return result
'''


async def change_date(excursion_id: int, new_date: str):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(date=new_date))
        await session.commit()


async def change_time(excursion_id: int, new_time: str):
    async with async_session() as session:
        new_time += ":00"
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(time=new_time))
        await session.commit()


async def change_people(excursion_id: int, people_type: str, new_people: str):
    async with async_session() as session:
        if people_type == "free":
            await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(people_free=new_people))
        elif people_type == "discount":
            await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(people_discount=new_people))
        elif people_type == "full":
            await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(people_full=new_people))
        await session.commit()


async def change_contacts(excursion_id: int, new_contacts: str):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(contacts=new_contacts))
        await session.commit()


async def change_from_place(excursion_id: int, new_from_place: str):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(from_place=new_from_place))
        await session.commit()


async def change_money(excursion_id: int, new_money: int):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(money=new_money))
        await session.commit()


async def change_eat(excursion_id: int, new_eat: int):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(eat=new_eat))
        await session.commit()


async def change_additional_info(excursion_id: int, new_additional_info: str):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(additional_info=new_additional_info))
        await session.commit()


async def change_mk(excursion_id: int, new_mk: str):
    async with async_session() as session:
        await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(mk=new_mk))
        await session.commit()


async def change_university(excursion_id: int):
    async with async_session() as session:
        if (await get_excursion(excursion_id)).university:
            await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(university=False))
        else:
            await session.execute(update(Excursion).where(Excursion.id == excursion_id).values(university=True))
        await session.commit()


async def get_report_exc() -> [ExcursionReport]:
    async with async_session() as session:
        result = await session.scalars(select(ExcursionReport))
        return result


async def update_food(excursion_id: int, complex_number: int, new_type_number: str, new_amount: int):
    async with async_session() as session:
        if complex_number == 1:
            query = update(Excursion).where(Excursion.id == excursion_id).values(eat1_type=new_type_number, eat1_amount=new_amount)
        else:
            query = update(Excursion).where(Excursion.id == excursion_id).values(eat2_type=new_type_number, eat2_amount=new_amount)
        await session.execute(query)
        await session.commit()


async def add_user(telegram_id: int, name: str, admin: bool):
    async with async_session() as session:
        temp_admin = 0
        if admin:
            temp_admin = 1

        query1 = insert(User).values(
            telegram_id=telegram_id,
            name=name,
            is_admin=temp_admin
        )

        await session.execute(query1)
        await session.commit()

        user_id = (await get_user(telegram_id)).id

        query2 = insert(Statistic).values(
            user_id=user_id,
            amount_groups=0,
            amount_individuals=0,
            start_date=datetime.datetime.today()
        )

        query3 = insert(Schedule).values(
            user_id=user_id,
            mon="?",
            tue="?",
            wed="?",
            thu="?",
            fri="?",
            sat="?",
            sun="?"
        )

        await session.execute(query2)
        await session.execute(query3)
        await session.commit()


async def get_report(date_from: str, date_to: str) -> Report:
    async with async_session() as session:
        excursions = await get_report_exc()

        university_people = 0
        people_free = 0
        people_full = 0
        people_discount = 0
        eats = []
        transfers = 0
        mks = []
        money = 0

        for exc in excursions:
            if compare_dates_interval(date_from, date_to, datetime.datetime.today().strftime("%d.%m.%Y")):
                print(True)
                if exc.university:
                    university_people += (exc.people_free + exc.people_full + exc.people_discount)
                people_free += exc.people_free
                people_full += exc.people_full
                people_discount += exc.people_discount
                if exc.eat:
                    pass
                if exc.mk:
                    mks.append(exc.mk)
                if exc.transfer:
                    transfers += 1
                money += exc.money

        return Report(people_free, people_discount, people_full, university_people, money, eats, mks, transfers)


async def recalculate_cost(excursion_id: int):
    exc = await get_excursion(excursion_id)
    temp = 0
    if exc.is_group:
        temp = 300 * (exc.people_discount + exc.people_full)
    else:
        if exc.people_discount + exc.people_full >= 10:
            temp = 450 * exc.people_full + 400 * exc.people_discount
        elif 6 <= exc.people_discount + exc.people_full <= 10:
            temp = 600 * exc.people_full + 400 * exc.people_discount
        elif 4 <= exc.people_discount + exc.people_full <= 5:
            temp = 3000
        else:
            temp = 2500
    async with async_session() as session:
        query = update(Excursion).where(Excursion.id == excursion_id).values(money=temp)
        await session.execute(query)
        await session.commit()