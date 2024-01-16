class Excursion:
    def __init__(self):
        self.id = None
        self.time = None
        self.date = None
        self.people = None
        self.contacts = None
        self.additional_info = None
        self.eat = None
        self.transfer = None
        self.mk = None
        self.from_place = None
        self.university = None
        self.money = None

    def __str__(self):
        return f"{self.id}: {self.date}, {self.time}\n" \
               f"Amount: {self.people}, Contacts: {self.contacts}\n" \
               f"University: {self.university}, Start: {self.from_place}\n" \
               f"Transfer: {self.transfer}, Food: {self.eat}\n" \
               f"MC: {self.mk}\n" \
               f"Additional info: {self.additional_info}\n"


class Report:
    def __init__(self, people, university_people, money, eats, mks, transfers):
        self.people = people
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
               f"Количество человек, посетивших ОЭЗ: {self.people}\n" \
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

    exc.people = int(row[5])

    if 1 <= exc.people <= 3:
        exc.money = 2500
    elif 4 <= exc.people <= 5:
        exc.money = 3000
    elif 6 <= exc.people <= 10:
        exc.money = int(exc.people) * 600
    else:
        exc.money = int(exc.people) * 300

    exc.contacts = row[6] + ", " + row[2]

    if row[7] == 'Не нужно':
        exc.eat = 0
    elif '1' in row[7]:
        exc.eat = 1
    elif '2' in row[7]:
        exc.eat = 2
    elif '3' in row[7]:
        exc.eat = 3

    if row[8] == 'Не нужен':
        exc.transfer = False
    else:
        exc.time = True

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

    return exc
