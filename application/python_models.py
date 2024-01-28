class Excursion:
    def __init__(self):
        self.id = None
        self.time = None
        self.date = None
        # self.people =
        self.people_free = None
        self.people_discount = None
        self.people_full = None
        self.contacts = None
        self.additional_info = None
        # self.eat = None
        self.eat1_type = None
        self.eat1_amount = None
        self.eat2_type = None
        self.eat2_amount = None
        self.transfer = None
        self.mk = None
        self.from_place = None
        self.university = None
        self.money = None

        self.is_group = None

    def __str__(self):
        message_food = f'\n{self.eat1_type}: {self.eat1_amount} чел.\n{self.eat2_type}: {self.eat2_amount} чел.'
        if self.eat1_amount <= self.eat2_amount <= 0:
            message_food = 'отсутствует'
        message = f"Информация по выбранной экскурсии ({self.id}):\n" \
                  f"Время: {self.date}, {':'.join(str(self.time).split(':')[:2])}\n" \
                  f"Гиды: подробности в тг-боте\n"
        message += f"Количество человек: {self.people_free + self.people_discount + self.people_full}\n" \
                   f"Старт: {self.from_place}\n" \
                   f"Университет: {'+' if self.university == 1 else '-'}\n" \
                   f"Контакт: {self.contacts}\n" \
                   f"МК: {self.mk}\n" \
                   f"------------------------------\nПитание: {message_food}\n------------------------------\n" \
                   f"Стоимость: {self.money}\n" \
                   f"Доп. Информация: {self.additional_info if self.additional_info != '-' else 'Отсутствует'}\n\n"
        return message


class Report:
    def __init__(self, people_free, people_discount, people_full, university_people, money, eats, mks, transfers):
        self.people_free = people_free
        self.people_full = people_full
        self.people_discount = people_discount
        self.university_people = university_people
        self.money = money
        self.eats = eats
        self.mks = mks
        self.transfers = transfers

    def __str__(self):
        food_message = ''
        for unique_type in set(self.eats):
            food_message += f"{str(unique_type)}: " + str(self.eats.count(unique_type)) + "\n"

        mks_message = ''
        for unique_type in set(self.mks):
            mks_message += f"{str(unique_type)}: " + str(self.mks.count(unique_type)) + "\n"

        return f"Количество человек, посетивших университет: {self.university_people}\n" \
               f"Количество человек, посетивших ОЭЗ: {(self.people_full + self.people_discount + self.people_free)}\n" \
               f"Количество проведённых мастер-классов: {len(self.mks)}\n" \
               f"Количество трансферов: {self.transfers}\n" \
               f"Оплата за экскурсии: {self.money}\n\n" \
               f"Детализация питания:\n" \
               f"{food_message}\n" \
               f"Детализация мастер-классов:\n" \
               f"{mks_message}"


async def parseRow(row: [str]) -> Excursion:
    exc = Excursion()

    exc.id = int(row[0])

    exc.date = row[3]

    exc.time = row[4]

    if len(exc.time.split(':')[0]) == 1:
        exc.time = '0' + exc.time

    exc.people_free = int(row[5])

    exc.contacts = row[6] + ", " + row[2]

    exc.eat1_type = row[7]

    if row[8].lower() == 'нет':
        exc.transfer = False
    else:
        exc.transfer = True

    try:
        if row[9]:
            exc.additional_info = row[9]
        else:
            exc.additional_info = "-"
    except Exception:
        exc.additional_info = "-"

    exc.mk = row[10]

    if row[11] == 'Да':
        exc.university = True
    else:
        exc.university = False

    exc.from_place = row[12]

    exc.people_full = int(row[13])

    exc.people_discount = int(row[14])

    exc.eat1_amount = int(row[15])

    exc.eat2_type = row[16]

    exc.eat2_amount = int(row[17])

    if row[18] == "Да" or row[18] == "Благотворительность":
        exc.is_group = True
    else:
        exc.is_group = False

    if exc.is_group:
        exc.money = 450 * exc.people_full + 400 * exc.people_discount
    else:
        if exc.people_discount + exc.people_full + exc.people_free >= 10:
            exc.money = 450 * exc.people_full + 400 * exc.people_discount
        elif 6 <= exc.people_discount + exc.people_full + exc.people_free <= 9:
            exc.money = 600 * exc.people_full + 500 * exc.people_discount
        elif 3 <= exc.people_discount + exc.people_full + exc.people_free <= 5:
            exc.money = 3000
        else:
            exc.money = 2500

    if row[18] == "Благотворительность":
        exc.money = 0

    return exc
