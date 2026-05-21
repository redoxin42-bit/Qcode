# Путь: master/handlers.py
import os
import shutil
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import database.db as db
import master.manager as manager
from master.states import AuthStates, AdminStates
from config import ADMIN_ID, USER_INSTANCES_DIR

router = Router()

# Главная клавиатура
def main_kb(is_admin: bool):
    buttons = [
        [InlineKeyboardButton(text="🔌 Подключить Qcode", callback_data="connect_ub")],
        [InlineKeyboardButton(text="⚙️ Панель управления", callback_data="control_panel")],
        [InlineKeyboardButton(text="📋 Логи", callback_data="view_logs")],
        [InlineKeyboardButton(text="🗑️ Удалить сессию", callback_data="delete_session")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура управления
def control_kb(status: str):
    buttons = []
    if status == "online":
        buttons.append([InlineKeyboardButton(text="⏸️ Остановить", callback_data="stop_ub")])
    else:
        buttons.append([InlineKeyboardButton(text="▶️ Запустить", callback_data="start_ub")])
    
    buttons.append([InlineKeyboardButton(text="🔄 Перезапустить", callback_data="restart_ub")])
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="go_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Админ клавиатура
def admin_kb():
    buttons = [
        [InlineKeyboardButton(text="🎁 Раздать подписку ВСЕМ", callback_data="sub_all")],
        [InlineKeyboardButton(text="👤 Управление юзером по ID", callback_data="manage_user_id")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await db.add_or_update_user(user_id)
        user = await db.get_user(user_id)
        
    is_admin = (user_id == ADMIN_ID)
    await message.answer("👋 Привет! Я Мастер-Бот управления твоим **Qcode UserBot**.", reply_markup=main_kb(is_admin))

# --- АДМИН ПАНЕЛЬ ---
@router.message(Command("adm"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("👑 **Админ-панель Qcode**", reply_markup=admin_kb())

@router.callback_query(F.data == "sub_all")
async def admin_sub_all(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await db.set_sub_to_all(1)
    await callback.answer("✅ Подписка выдана всем зарегистрированным пользователям!", show_alert=True)

@router.callback_data(F.data == "manage_user_id")
async def admin_manage_uid(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("Введите Telegram ID пользователя:")
    await state.set_state(AdminStates.waiting_for_user_id)
    await callback.answer()

@router.message(AdminStates.waiting_for_user_id)
async def admin_user_card(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    try:
        tgt_id = int(message.text)
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return
    
    user = await db.get_user(tgt_id)
    if not user:
        await message.answer("❌ Пользователь не найден в БД.")
        await state.clear()
        return
    
    await state.clear()
    sub_status = "Есть" if user[5] == 1 else "Нет"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать подписку", callback_data=f"give_sub_{tgt_id}")],
        [InlineKeyboardButton(text="➖ Забрать подписку", callback_data=f"take_sub_{tgt_id}")],
        [InlineKeyboardButton(text="🗑️ Стереть сессию", callback_data=f"force_del_{tgt_id}")]
    ])
    
    await message.answer(f"👤 **Карточка юзера {tgt_id}**\nПодписка: {sub_status}\nСтатус UB: {user[4]}", reply_markup=kb)

@router.callback_query(F.data.startswith("give_sub_"))
async def action_give_sub(callback: CallbackQuery):
    tgt_id = int(callback.data.split("_")[2])
    await db.add_or_update_user(tgt_id, has_sub=1)
    await callback.answer("Подписка успешно выдана!")

@router.callback_query(F.data.startswith("take_sub_"))
async def action_take_sub(callback: CallbackQuery):
    tgt_id = int(callback.data.split("_")[2])
    await db.add_or_update_user(tgt_id, has_sub=0)
    await manager.stop_ub_process(tgt_id)
    await db.add_or_update_user(tgt_id, status="offline")
    await callback.answer("Подписка аннулирована, юзербот остановлен.")

# --- ОБЩИЙ ФУНКЦИОНАЛ ---
@router.callback_query(F.data == "go_main")
async def go_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = (callback.from_user.id == ADMIN_ID)
    await callback.message.edit_text("👋 Привет! Я Мастер-Бот управления твоим **Qcode UserBot**.", reply_markup=main_kb(is_admin))

@router.callback_query(F.data == "control_panel")
async def control_panel(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if user_id != ADMIN_ID and (not user or user[5] == 0):
        await callback.answer("❌ У вас нет активной подписки. Обратитесь к админу.", show_alert=True)
        return
        
    status = user[4] if user else "not_configured"
    status_str = "🟢 Онлайн" if status == "online" else "🔴 Оффлайн"
    await callback.message.edit_text(f"⚙️ **Панель управления Qcode**\n\nТекущий статус: {status_str}", reply_markup=control_kb(status))

@router.callback_query(F.data == "start_ub")
async def start_ub_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if user[4] == "not_configured":
        await callback.answer("❌ Сначала пройдите авторизацию через кнопку 'Подключить Qcode'", show_alert=True)
        return
        
    await callback.message.edit_text("⏳ Запуск юзербота...")
    await manager.start_ub_process(user_id)
    await db.add_or_update_user(user_id, status="online")
    await callback.message.edit_text("⚙️ **Панель управления Qcode**\n\nТекущий статус: 🟢 Онлайн", reply_markup=control_kb("online"))

@router.callback_query(F.data == "stop_ub")
async def stop_ub_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await manager.stop_ub_process(user_id)
    await db.add_or_update_user(user_id, status="offline")
    await callback.message.edit_text("⚙️ **Панель управления Qcode**\n\nТекущий статус: 🔴 Оффлайн", reply_markup=control_kb("offline"))

@router.callback_query(F.data == "view_logs")
async def view_logs_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    logs = manager.get_logs(user_id)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="go_main")]])
    # Отправляем логи моноширинным текстом
    await callback.message.edit_text(f"📋 **Последние логи системы:**\n\n<code>{logs}</code>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "delete_session")
async def delete_session_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await manager.stop_ub_process(user_id)
    
    user_dir = os.path.join(USER_INSTANCES_DIR, f"user_{user_id}")
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
        
    await db.add_or_update_user(user_id, status="not_configured", api_id=0, api_hash="", phone="")
    await callback.answer("🗑️ Все файлы вашей сессии полностью удалены.", show_alert=True)
    is_admin = (user_id == ADMIN_ID)
    await callback.message.edit_text("👋 Привет! Я Мастер-Бот управления твоим **Qcode UserBot**.", reply_markup=main_kb(is_admin))
