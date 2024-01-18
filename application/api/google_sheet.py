import gspread
from gspread.spreadsheet import Spreadsheet
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from application.python_models import parseRow, Excursion


class Connection:
    def __init__(self):
        self.scope = ['https://www.googleapis.com/auth/spreadsheets',
                      'https://www.googleapis.com/auth/drive']

        self.credentials = ServiceAccountCredentials.from_json_keyfile_name("gs_key.json", self.scope)
        self.client = None

    async def auth(self):
        client = gspread.authorize(self.credentials)
        self.client = client


connection = Connection()


async def authenticate():
    await connection.auth()


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
    worksheet = (await getWorkbook("Excursions")).sheet1
    idx = 2
    for excursion in await get_rows("Excursions"):
        exc = await parseRow(excursion)
        if datetime.strptime(exc.date + ' ' + exc.time, "%d.%m.%Y %H:%M:%S") <= datetime.now():
            worksheet.delete_row(idx)
        idx += 1



