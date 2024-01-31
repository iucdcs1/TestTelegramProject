import asyncio
import os

import gspread
from gspread.spreadsheet import Spreadsheet
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from application.python_models import parseRow, Excursion
from googleapiclient.discovery import build


class Connection:
    def __init__(self):
        self.scope = ['https://www.googleapis.com/auth/spreadsheets',
                      'https://www.googleapis.com/auth/drive',
                      'https://www.googleapis.com/auth/calendar']

        self.credentials = ServiceAccountCredentials.from_json_keyfile_name("gs_key.json", self.scope)
        self.client = None
        self.service = None
        self.calendar_token = None

    async def auth(self):
        client = gspread.authorize(self.credentials)
        self.client = client
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.calendar_token = os.getenv("CALENDAR_ID")


connection = Connection()


async def authenticate():
    await connection.auth()


async def getCalendarItems():
    result = await asyncio.to_thread(connection.service.events().list(calendarId=connection.calendar_token).execute)
    return result.get("items", [])


async def getCalendarExcursion(exc: Excursion):
    items = await getCalendarItems()
    eventId = -1

    for item in items:
        if int(item['summary'].split(', ')[3]) == exc.id:
            eventId = item['id']
            break

    if eventId != -1:
        event = await asyncio.to_thread(
            connection.service.events().get(calendarId=connection.calendar_token, eventId=eventId).execute)
        return event
    else:
        return None


async def editCalendarEvent(exc: Excursion):
    from application.utilities.tools import construct_message
    event = await getCalendarExcursion(exc)

    message = await construct_message(exc.id)

    event['description'] = message

    event['start']['dateTime'] = datetime.strptime(exc.date + " " + exc.time, "%d.%m.%Y %H:%M:%S").isoformat()
    event['end']['dateTime'] = (datetime.strptime(exc.date + " " + exc.time, "%d.%m.%Y %H:%M:%S") + timedelta(hours=1,
                                                                                                              minutes=30)).isoformat()

    connection.service.events().update(calendarId=connection.calendar_token, eventId=event['id'], body=event).execute()


async def addExcursionToCalendar(exc: Excursion):
    from application.utilities.tools import construct_message
    event = {
        'summary': f'Экскурсия, {exc.contacts}, {exc.id}',
        'location': 'г. Иннополис',
        'description': f'{await construct_message(exc.id)}',
        'start': {
            'dateTime': datetime.strptime(exc.date + " " + exc.time, "%d.%m.%Y %H:%M:%S").isoformat(),
            'timeZone': 'Europe/Moscow'
        },
        'end': {
            'dateTime': (datetime.strptime(exc.date + " " + exc.time, "%d.%m.%Y %H:%M:%S") + timedelta(hours=1,
                                                                                                       minutes=30)).isoformat(),
            'timeZone': 'Europe/Moscow'
        },
        'reminders': {'useDefault': True}
    }
    connection.service.events().insert(calendarId=connection.calendar_token, body=event).execute()


def debugCalendarItems(items: []) -> str:
    return str(items[0]['summary']) + "\n" + str(items[0]["description"])


async def getWorkbook(name: str) -> Spreadsheet:
    workbook = connection.client.open(name)
    return workbook


async def get_rows(name: str) -> []:
    workbook = await getWorkbook(name)
    sheet = workbook.sheet1
    rows = []
    amount = 0
    while True:
        temp = sheet.row_values(amount + 2)
        if len(temp) > 0:
            rows.append(temp)
            amount += 1
        else:
            break
    return rows


async def remove_calendar_excursion(exc: Excursion):
    event = await getCalendarExcursion(exc)
    await asyncio.to_thread(
        connection.service.events().delete(calendarId=connection.calendar_token, eventId=event['id']).execute)


async def get_excursions_from_sheet() -> [Excursion]:
    result = []
    worksheet = (await getWorkbook("Excursions")).sheet1
    backup_sheet = (await getWorkbook("Excursions")).get_worksheet_by_id(306307666)
    await remove_past_excursions()
    idx = 2
    for excursion in await get_rows("Excursions"):
        exc = await parseRow(excursion)
        result.append(exc)
        backup_sheet.append_row(excursion)
        worksheet.delete_row(idx)
    return result


async def remove_past_excursions():
    # Spreadsheets

    worksheet = (await getWorkbook("Excursions")).sheet1
    idx = 2
    for excursion in await get_rows("Excursions"):
        exc = await parseRow(excursion)
        if datetime.strptime(exc.date + ' ' + exc.time, "%d.%m.%Y %H:%M:%S") <= datetime.now():
            worksheet.delete_row(idx)
        idx += 1

    # Calendar

    events = await getCalendarItems()

    for event in events:
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        event_start_datetime = datetime.fromisoformat(event_start).replace(tzinfo=None)
        if event_start_datetime < datetime.now() - timedelta(hours=1, minutes=30):
            await asyncio.to_thread(
                connection.service.events().delete(calendarId=connection.calendar_token, eventId=event['id']).execute)
