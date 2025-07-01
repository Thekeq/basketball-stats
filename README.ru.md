# Telegram Basketball Stats Bot 🏀

👉 [Read in English](README.md)

Простой Telegram-бот для ведения статистики бросков (трешки и штрафные).

## Функционал

- Добавление статистики бросков `/add_shots`
- Просмотр статистики с графиками `/threepoint_stats`, `/freethrow_stats`
- Удаление записей `/delete_shot`
- Просмотр средней статистики `/avg_stats`
- Переключение языка `/language` (русский/английский)

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```
3. Создайте `.env` и добавьте туда токен бота:
    ```
    BOT_TOKEN=your_telegram_bot_token
    ```
4. Запустите бота:
    ```bash
    python main.py
    ```

## Зависимости

- Python 3.10+
- aiogram
- matplotlib
- python-dotenv

---

Если нужны будут подсказки или помощь — обращайтесь!
