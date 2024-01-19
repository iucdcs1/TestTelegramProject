import os

from dotenv import load_dotenv
from sqlalchemy import BigInteger, ForeignKey, DATE, TIME, BOOLEAN, VARCHAR, INTEGER
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

load_dotenv(".env")
url = os.getenv("SQLALCHEMY_URL")

engine = create_async_engine(url, echo=True)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id = mapped_column(BigInteger)
    is_admin: Mapped[bool] = mapped_column()
    name: Mapped[str] = mapped_column()


class Excursion(Base):
    __tablename__ = "excursions"

    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[str] = mapped_column()
    date: Mapped[str] = mapped_column()
    guide: Mapped[str] = mapped_column(nullable=True)
    # people: Mapped[int] = mapped_column()
    people_free: Mapped[int] = mapped_column()
    people_discount: Mapped[int] = mapped_column()
    people_full: Mapped[int] = mapped_column()
    from_place = mapped_column(VARCHAR)
    university = mapped_column(BOOLEAN)
    contacts: Mapped[str] = mapped_column()
    money = mapped_column(INTEGER)
    # eat: Mapped[int] = mapped_column(ForeignKey('foods.id'), nullable=True)
    eat1_type: Mapped[str] = mapped_column()
    eat1_amount: Mapped[int] = mapped_column()
    eat2_type: Mapped[str] = mapped_column()
    eat2_amount: Mapped[int] = mapped_column()
    mk: Mapped[str] = mapped_column(nullable=True)
    transfer: Mapped[bool] = mapped_column(BOOLEAN, nullable=True)
    additional_info: Mapped[str] = mapped_column()
    is_group: Mapped[bool] = mapped_column(BOOLEAN)


class ExcursionReport(Base):
    __tablename__ = "excursions_report"

    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[str] = mapped_column()
    date: Mapped[str] = mapped_column()
    # people: Mapped[int] = mapped_column()
    people_free: Mapped[int] = mapped_column()
    people_discount: Mapped[int] = mapped_column()
    people_full: Mapped[int] = mapped_column()
    university = mapped_column(BOOLEAN)
    contacts: Mapped[str] = mapped_column()
    money = mapped_column(INTEGER)
    # eat: Mapped[int] = mapped_column(ForeignKey('foods.id'), nullable=True)
    eat1_type: Mapped[str] = mapped_column()
    eat1_amount: Mapped[int] = mapped_column()
    eat2_type: Mapped[str] = mapped_column()
    eat2_amount: Mapped[int] = mapped_column()
    mk: Mapped[str] = mapped_column(nullable=True)
    transfer: Mapped[bool] = mapped_column(BOOLEAN, nullable=True)
    additional_info: Mapped[str] = mapped_column()
    is_group: Mapped[bool] = mapped_column(BOOLEAN)
    finished: Mapped[bool] = mapped_column(BOOLEAN, nullable=True)


class Statistic(Base):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount_groups: Mapped[int] = mapped_column()
    amount_individuals: Mapped[int] = mapped_column()
    start_date = mapped_column(DATE)


class Schedule(Base):
    __tablename__ = "timetables"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    mon: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    tue: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    wed: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    thu: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    fri: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    sat: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    sun: Mapped[str] = mapped_column(VARCHAR, nullable=True)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
