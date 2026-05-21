# Путь: master/states.py
from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    waiting_for_api = State()       # Ожидание строки: "api_id:api_hash"
    waiting_for_phone = State()     # Ожидание номера телефона
    waiting_for_code = State()      # Ожидание кода подтверждения
    waiting_for_2fa = State()       # Ожидание пароля двухфакторки (если есть)

class AdminStates(StatesGroup):
    waiting_for_user_id = State()   # Ожидание ID юзера для управления подпиской
