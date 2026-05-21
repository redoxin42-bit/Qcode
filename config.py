# Путь: config.py
import os

TOKEN = "8198575429:AAEzgX1vxCZfABrwhZEXOf48kRdYv4_s3yY"
ADMIN_ID = 8624430245  # ЗАМЕНИ ТУТ НА СВОЙ ТЕЛЕГРАМ ID

# Создаем необходимые папки при старте
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_INSTANCES_DIR = os.path.join(BASE_DIR, "user_instances")
DB_DIR = os.path.join(BASE_DIR, "database")

os.makedirs(USER_INSTANCES_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "qcode.db")
