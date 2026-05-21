# Путь: config.py
import os

# Новый токен твоего Мастер-Бота
TOKEN = "8198575429:AAEzgX1vxCZfABrwhZEXOf48kRdYv4_s3yY"

# Твой личный Telegram ID для админки (взят с твоего скриншота)
ADMIN_ID = 8624430245

# Автоматическое определение путей к папкам проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_INSTANCES_DIR = os.path.join(BASE_DIR, "user_instances")
DB_DIR = os.path.join(BASE_DIR, "database")

# Авто-создание папок при старте, если их еще нет в системе
os.makedirs(USER_INSTANCES_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Путь к файлу базы данных SQLite
DB_PATH = os.path.join(DB_DIR, "qcode.db")
