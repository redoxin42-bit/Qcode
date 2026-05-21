# Путь: user_instances/main_ub.py
import sys
import os
import asyncio
import logging
import re
import importlib.util
import sqlite3
from telethon import TelegramClient, events
from telethon.tl.functions.account import GetAuthorizationsRequest

if len(sys.argv) < 2:
    sys.exit("Ошибка: ID пользователя не передан.")

USER_ID = sys.argv[1]
USER_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(USER_DIR, f"user_{USER_ID}", "modules")
LOG_PATH = os.path.join(USER_DIR, f"user_{USER_ID}", "logs.txt")
DB_PATH = os.path.join(USER_DIR, "..", "database", "qcode.db")

os.makedirs(MODULES_DIR, exist_ok=True)

# Настройка логирования в файл юзера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8")]
)

# Чтение API данных из SQLite БД
def get_api_credentials():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT api_id, api_hash FROM users WHERE user_id = ?", (USER_ID,))
    res = cursor.fetchone()
    conn.close()
    return res

credentials = get_api_credentials()
if not credentials or not credentials[0]:
    logging.error("API данные не найдены в БД.")
    sys.exit()

API_ID, API_HASH = credentials[0], credentials[1]
session_file = os.path.join(USER_DIR, f"user_{USER_ID}", "qcode")

client = TelegramClient(session_file, API_ID, API_HASH)

# Хранилище динамически загруженных модулей {название: объект_модуля}
loaded_modules = {}

# --- ДЕТЕКТОР ВИРУСОВ И КРАЖИ СЕССИЙ (АНАЛИЗАТОР .py) ---
def check_for_viruses(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()
    
    # Опасные сигнатуры (Попытки угнать сессию, скрытый код, запросы налево)
    dangerous_patterns = {
        r"\.session": "Попытка доступа к файлам сессий Telegram",
        r"telethon.*session": "Подозрительный перехват сессии Telethon",
        r"pyrogram.*session": "Подозрительный перехват сессии Pyrogram",
        r"shutil\.copy": "Попытка несанкционированного копирования файлов",
        r"os\.system|subprocess|eval\(|exec\(": "Скрытый запуск системных команд (бэкдор)",
        r"requests\.|aiohttp\.|httpx\.": "Скрытая отправка данных на внешние сервера",
        r"bot.*send|sendMessage": "Попытка слить лог/данные в чужого бота"
    }
    
    for pattern, description in dangerous_patterns.items():
        if re.search(pattern, code, re.IGNORECASE):
            return True, description
    return False, None

# --- ДЕТЕКТОР КРАЖИ СЕССИИ (SESSION GUARD) ---
async def session_guard_task(initial_count):
    logging.info("Детектор кражи сессий запущен.")
    while True:
        await asyncio.sleep(600)  # Проверка каждые 10 минут
        try:
            authorizations = await client(GetAuthorizationsRequest())
            current_count = len(authorizations.authorizations)
            if current_count > initial_count:
                await client.send_message(
                    "me", 
                    "🚨 **ДЕТЕКТОР КРАЖИ СЕССИИ Qcode!**\n\n"
                    "Внимание! В вашем аккаунте появилось **новое активное устройство**.\n"
                    "Если это не вы, немедленно завершите все сессии в настройках конфиденциальности Telegram!"
                )
                initial_count = current_count
        except Exception as e:
            logging.error(f"Ошибка в Session Guard: {e}")

# --- КОМАНДА ЗАГРУЗКИ СКРИПТОВ (.dls) ---
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.dls$"))
async def download_script(event):
    if not event.is_reply:
        await event.edit("❌ Ответьте этой командой (`.dls`) реплаем на файл `.py`!")
        return
        
    reply_msg = await event.get_reply_message()
    if not reply_msg.media or not reply_msg.file or not reply_msg.file.name.endswith(".py"):
        await event.edit("❌ Реплай должен быть строго на файл с расширением `.py`!")
        return

    mod_name = reply_msg.file.name
    temp_path = os.path.join(MODULES_DIR, f"temp_{mod_name}")
    final_path = os.path.join(MODULES_DIR, mod_name)

    await event.edit("⏳ Скачивание и проверка скрипта антивирусом Qcode...")
    await client.download_media(reply_msg, temp_path)

    # Проверка на вирусы
    is_virus, threat_type = check_for_viruses(temp_path)
    if is_virus:
        os.remove(temp_path)
        await event.edit(f"🚨 **АНТИВИРУС Qcode ЗАБЛОКИРОВАЛ ФАЙЛ!**\n\nУгроза: `{threat_type}`\nЗагрузка скрипта полностью отменена ради безопасности аккаунта.")
        logging.warning(f"Заблокирован вредоносный модуль {mod_name}. Угроза: {threat_type}")
        return

    # Перемещаем в постоянную папку, если всё чисто
    if os.path.exists(final_path):
        os.remove(final_path)
    os.rename(temp_path, final_path)

    # Динамический импорт скрипта в память
    try:
        spec = importlib.util.spec_from_file_location(mod_name[:-3], final_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        loaded_modules[mod_name[:-3]] = module
        await event.edit(f"✅ **Модуль `[ {mod_name[:-3]} ]` успешно загружен!**\nИспользуйте `.help` для просмотра.")
        logging.info(f"Успешно импортирован кастомный модуль: {mod_name}")
    except Exception as e:
        await event.edit(f"❌ Ошибка компиляции скрипта: `{e}`")
        if os.path.exists(final_path): os.remove(final_path)

# --- КОМАНДА ПОМОЩИ (.help) ---
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.help$"))
async def help_handler(event):
    if not loaded_modules:
        await event.edit("📋 **Панель Qcode**\n\nКастомные скрипты не загружены. Загрузите через `.dls` (реплаем на `.py`).")
        return
        
    text = "📋 **Доступные скрипты в панели Qcode:**\n\n"
    for name, mod in loaded_modules.items():
        # Берем описание скрипта из его docstring (тройных кавычек в начале файла)
        description = mod.__doc__ if mod.__doc__ else "Описание отсутствует."
        text += f"🔹 **{name}**\nDescription: _{description}_\nЗапустить: `.run {name}`\n\n"
        
    await event.edit(text)

# --- КОМАНДА ЗАПУСКА СКРИПТА (.run <название>) ---
@client.on(events.NewMessage(outgoing=True, pattern=r"^\.run\s+(.+)$"))
async def run_handler(event):
    mod_name = event.pattern_match.group(1).strip()
    
    if mod_name not in loaded_modules:
        await event.edit(f"❌ Скрипт `{mod_name}` не найден. Сверьтесь с `.help`")
        return
        
    module = loaded_modules[mod_name]
    
    # Скрипт должен содержать асинхронную функцию 'run(client, event)'
    if hasattr(module, "run"):
        await event.edit(f"🚀 Запуск скрипта `{mod_name}`...")
        try:
            await module.run(client, event)
        except Exception as e:
            await event.respond(f"❌ Ошибка выполнения скрипта `{mod_name}`: `{e}`")
            logging.error(f"Ошибка внутри {mod_name}: {e}")
    else:
        await event.edit(f"❌ В скрипте `{mod_name}` отсутствует точка входа (функция `async def run`).")

# --- СТАРТ ЮЗЕРБОТА ---
async def start_ub():
    logging.info(f"Запуск экземпляра Юзербота для ID {USER_ID}...")
    await client.start()
    
    # Получаем начальное число сессий для детектора кражи
    try:
        authorizations = await client(GetAuthorizationsRequest())
        initial_sessions = len(authorizations.authorizations)
    except Exception:
        initial_sessions = 1
        
    # Запускаем фоновый таск детектора сессий
    asyncio.create_task(session_guard_task(initial_sessions))
    
    logging.info("Юзербот успешно подключен и вошел в сеть.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_ub())
