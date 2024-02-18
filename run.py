import asyncio
import logging
import os
import sys

from aiogram import Dispatcher, Bot
from dotenv import load_dotenv

from application.api.google_apis import authenticate
from application.database.models import async_main
from application.database.requests import get_users
from application.handlers import router
from application.middlewares import CounterMiddleware
from application.utilities.scheduler import setup_scheduler


logging.basicConfig(format='\n%(asctime)s,%(msecs)d n%(name)s, %(levelname)s:\n%(message)s', level=logging.INFO, stream=sys.stdout)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.ERROR)

logging.getLogger("googleapiclient.discovery").setLevel(logging.ERROR)

logging.getLogger('sqlalchemy').propagate = False
logging.getLogger('sqlalchemy.engine.Engine').propagate = False


token = os.getenv("TOKEN_API")
bot = Bot(token, parse_mode="HTML")
dp = Dispatcher()


async def notify_user(telegram_id, message):
    try:
        await bot.send_message(telegram_id, message)
    except Exception:
        logging.error(f'Error sending message to: {telegram_id}, message: {message}')


async def main() -> None:
    await async_main()
    load_dotenv(".env")
    await authenticate()

    temporary_users = await get_users()
    router.message.middleware(CounterMiddleware(temporary_users))

    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    scheduler = await setup_scheduler()

    try:
        scheduler.start()
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
