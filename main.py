import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, CallbackQuery, \
    BufferedInputFile
from dotenv import load_dotenv
from db import DataBase
from text import msg
from io import BytesIO
import os
import matplotlib.pyplot as plt

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
router = Router()
db = DataBase("data.db")


@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id

    if not db.user_exists(user_id):  # Проверка на существование пользователя
        db.add_user(user_id, "en")
        await message.reply(msg.get("start_en"))
    else:
        lang = db.user_language(user_id)
        await message.reply(msg.get(f"start_{lang}", msg["start_en"]))


@router.message(Command("language"))  # Смена языка
async def language(message: Message):
    user_id = message.from_user.id
    db.change_language(user_id)
    lang = db.user_language(user_id)
    await message.reply(msg.get(f"language_{lang}", msg["language_en"]))


@router.message(Command("add_shots"))  # Ввод данных для статистики
async def add_shots(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = db.user_language(user_id)
    await message.answer({
                             "en": "Enter data in the format: 'YYYY-MM-DD, freethrow/threepoint, 85'",
                             "ru": "Введите данные в формате: '2024-09-19, штрафные/трешки, 85'"
                         }[lang])
    await state.set_state("waiting_for_shot_data")


@router.message(StateFilter("waiting_for_shot_data"))  # Сохранение статистики
async def save_shots(message: Message, state: FSMContext):
    try:
        date_str, shot_type, made_str = [x.strip() for x in message.text.split(",")]
        if shot_type not in ["трешки", "штрафные", "threepoint", "freethrow"]:
            raise ValueError("Invalid shot type")

        made = int(made_str)

        if shot_type == "freethrow":
            shot_type = "штрафные"
        elif shot_type == "threepoint":
            shot_type = "трешки"

        db.add_shot(message.from_user.id, date_str, shot_type, made)
        await message.answer("Данные успешно сохранены!" if db.user_language(
            message.from_user.id) == "ru" else "Data saved successfully!")

    except Exception as e:
        await message.answer("Неверный формат. Попробуйте снова." if db.user_language(
            message.from_user.id) == "ru" else "Invalid format. Please try again.")
    finally:
        await state.clear()


@router.message(Command(commands=["threepoint_stats", "freethrow_stats"]))  # Показ графика
async def stats_handler(message: Message):
    user_id = message.from_user.id
    lang = db.user_language(user_id)

    # Определяем тип броска и заголовок в зависимости от команды
    if message.text.startswith("/threepoint_stats"):
        shot_type_ru = "трешки"
        shot_type_en = "threepoint"
        title_ru = "Трёшки"
        title_en = "Three-pointers"
        ylabel_ru = "Кол-во попаданий"
        ylabel_en = "Made shots"
        xlabel_ru = "Дата"
        xlabel_en = "Date"
    else:  # /freethrow_stats
        shot_type_ru = "штрафные"
        shot_type_en = "freethrow"
        title_ru = "Штрафные"
        title_en = "Free throws"
        ylabel_ru = "Кол-во попаданий"
        ylabel_en = "Made shots"
        xlabel_ru = "Дата"
        xlabel_en = "Date"

    data = db.get_shots_by_type(user_id, shot_type_ru) or db.get_shots_by_type(user_id, shot_type_en)
    if not data:
        await message.answer("Нет данных." if lang == "ru" else "No data available.")
        return

    dates = [row[0] for row in data]
    values = [row[1] for row in data]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, values, marker='o', color='blue')
    plt.ylim(0, 100)
    plt.xlabel(xlabel_ru if lang == "ru" else xlabel_en)
    plt.ylabel(ylabel_ru if lang == "ru" else ylabel_en)
    plt.title(title_ru if lang == "ru" else title_en)

    for i, (x, y) in enumerate(zip(dates, values)):
        plt.text(x, y + 2, f"{y}", ha='center', va='bottom', fontsize=9)

        if i > 0:
            diff = y - values[i - 1]
            perc = (diff / values[i - 1]) * 100 if values[i - 1] != 0 else 0
            color = 'green' if perc > 0 else 'red'
            sign = "+" if perc > 0 else ""
            plt.text(x, y - 6, f"{sign}{perc:.0f}%", ha='center', va='top', fontsize=8, color=color)

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    photo = BufferedInputFile(buf.read(), filename="stats.png")
    await message.answer_photo(photo=photo)


@router.message(Command("delete_shot"))  # Удалить статистку
async def delete_shot_start(message: Message):
    lang = db.user_language(message.from_user.id)

    text_ru = "Выберите тип броска для удаления:"
    text_en = "Choose shot type to delete:"

    btn_freethrow_ru = "Штрафные"
    btn_threepoint_ru = "Трешки"
    btn_freethrow_en = "Free throws"
    btn_threepoint_en = "Three-pointers"

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=btn_freethrow_ru if lang == "ru" else btn_freethrow_en,
                             callback_data="delete_type:штрафные"),
        InlineKeyboardButton(text=btn_threepoint_ru if lang == "ru" else btn_threepoint_en,
                             callback_data="delete_type:трешки")
    ]])

    await message.answer(text_ru if lang == "ru" else text_en, reply_markup=kb)


@router.callback_query(F.data.startswith("delete_type:"))  # Выбор статистики на удаление
async def delete_shot_show_records(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = db.user_language(user_id)

    shot_type = callback.data.split(":")[1]

    data = db.get_shots_by_type(user_id, shot_type)
    if not data:
        no_data_msg = "Данных для удаления нет." if lang == "ru" else "No data to delete."
        await callback.message.edit_text(no_data_msg)
        return

    buttons = [
        [InlineKeyboardButton(
            text=(f"Дата - {row[0]}, Попаданий - {row[1]}%" if lang == "ru" else f"Date - {row[0]}, Made - {row[1]}"),
            callback_data=f"delete_record:{shot_type}|{row[0]}|{row[1]}"
        )] for row in data
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    choose_msg = "Выберите данные для удаления:" if lang == "ru" else "Select data to delete:"
    await callback.message.edit_text(choose_msg, reply_markup=kb)


@router.callback_query(F.data.startswith("delete_record:"))  # Удаление статистики
async def delete_shot_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = db.user_language(user_id)

    data = callback.data[len("delete_record:"):].split("|")
    shot_type, date, made = data[0], data[1], int(data[2])

    deleted = db.delete_shot(user_id, date, shot_type, made)
    if deleted:
        success_msg = "Запись успешно удалена." if lang == "ru" else "Record successfully deleted."
        await callback.message.edit_text(success_msg)
    else:
        fail_msg = "Не удалось удалить запись." if lang == "ru" else "Failed to delete the record."
        await callback.message.edit_text(fail_msg)


@router.message(Command("avg_stats"))  # Средняя статистика
async def avg_stats_handler(message: Message):
    user_id = message.from_user.id
    lang = db.user_language(user_id)

    avg_free = db.get_average_shots(user_id, "штрафные") or 0
    avg_three = db.get_average_shots(user_id, "трешки") or 0

    text = (
        f"Средняя статистика штрафных: {avg_free:.2f}%\n"
        f"Средняя статистика трёшек: {avg_three:.2f}%"
    ) if lang == "ru" else (
        f"Average free throw stats: {avg_free:.2f}%\n"
        f"Average three-point stats: {avg_three:.2f}%"
    )

    await message.answer(text)


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    print("Telegram Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
