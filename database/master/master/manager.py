# Путь: master/manager.py
import asyncio
import os
import sys
import signal
from config import USER_INSTANCES_DIR

# Хранилище активных процессов {user_id: process_object}
active_processes = {}
# Хранилище потоков ввода для авторизации {user_id: StreamWriter}
active_inputs = {}

async def start_ub_process(user_id: int, setup_mode: bool = False):
    user_dir = os.path.join(USER_INSTANCES_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(os.path.join(user_dir, "modules"), exist_ok=True)
    
    log_file = open(os.path.join(user_dir, "logs.txt"), "a", encoding="utf-8")
    
    # Путь к исполняемому файлу нашего юзербота
    ub_script = os.path.join(os.path.dirname(USER_INSTANCES_DIR), "user_instances", "main_ub.py")
    
    # Запускаем как независимый подпроцесс
    proc = await asyncio.create_subprocess_exec(
        sys.executable, ub_script, str(user_id),
        cwd=user_dir,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    
    active_processes[user_id] = proc
    return proc

async def stop_ub_process(user_id: int):
    proc = active_processes.get(user_id)
    if proc:
        try:
            proc.terminate()
            await proc.wait()
        except Exception:
            pass
        active_processes.pop(user_id, None)
        active_inputs.pop(user_id, None)
        return True
    return False

def get_logs(user_id: int, lines_count: int = 20):
    user_dir = os.path.join(USER_INSTANCES_DIR, f"user_{user_id}")
    log_path = os.path.join(user_dir, "logs.txt")
    if not os.path.exists(log_path):
        return "Логи пока пустые."
    
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        return "".join(lines[-lines_count:])
