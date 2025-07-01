import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        # Создание таблицы, если она еще не существует
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    language TEXT
                )
            ''')
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS shots (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    type TEXT,
                    date TEXT,
                    made INTEGER
                )
            ''')

        self.connection.commit()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            return bool(len(result))

    def add_user(self, user_id, language):
        with self.connection:
            self.cursor.execute(
                "INSERT INTO users (`user_id`, `language`) VALUES (?, ?)",
                (user_id, language)
            )

    def user_language(self, user_id):
        with self.connection:
            result = self.cursor.execute(
                "SELECT `language` FROM `users` WHERE `user_id` = ?", (user_id,)
            ).fetchall()
            return result[0][0] if result else "en"

    def change_language(self, user_id):
        current = self.user_language(user_id)
        new_lang = "ru" if current == "en" else "en"

        with self.connection:
            self.cursor.execute(
                "UPDATE users SET language = ? WHERE user_id = ?", (new_lang, user_id)
            )

    def add_shot(self, user_id, date, shot_type, made):
        with self.connection:
            self.cursor.execute("INSERT INTO shots (user_id, date, type, made) VALUES (?, ?, ?, ?)",
                                (user_id, date, shot_type, made))

    def get_shots_by_type(self, user_id, shot_type):
        self.cursor.execute("SELECT date, made FROM shots WHERE user_id = ? AND type = ? ORDER BY date",
                            (user_id, shot_type))
        return self.cursor.fetchall()

    def delete_shot(self, user_id, date, shot_type, made):
        with self.connection:
            cursor = self.cursor.execute(
                "DELETE FROM shots WHERE user_id = ? AND date = ? AND type = ? AND made = ?",
                (user_id, date, shot_type, made)
            )
            return cursor.rowcount > 0

    def get_average_shots(self, user_id, shot_type):
        self.cursor.execute(
            "SELECT AVG(made) FROM shots WHERE user_id = ? AND type = ?",
            (user_id, shot_type)
        )
        result = self.cursor.fetchone()
        return result[0] if result and result[0] is not None else 0
