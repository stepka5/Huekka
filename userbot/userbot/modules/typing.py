import asyncio
import logging
from telethon import events
import os
import json

logger = logging.getLogger(__name__)

# Настройки пользователей
user_settings_file = "cash/typing_settings.json"

def load_settings():
    """Загружает настройки из файла"""
    if os.path.exists(user_settings_file):
        try:
            with open(user_settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
    return {}

def save_settings(settings):
    """Сохраняет настройки в файл"""
    try:
        with open(user_settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")

user_settings = load_settings()
default_delay = 0.08
default_cursor = "▮"

async def type_animation(event):
    """Анимация печати текста"""
    try:
        text = event.text.split('.п', 1)[1].strip()
        if not text:
            await event.edit("ℹ️ Введите текст после .п")
            return
        
        user_id = str(event.sender_id)
        delay = user_settings.get(user_id, {}).get('delay', default_delay)
        cursor = user_settings.get(user_id, {}).get('cursor', default_cursor)
        
        msg = await event.edit(cursor)
        typed = ""
        
        for char in text:
            typed += char
            await msg.edit(typed + cursor)
            await asyncio.sleep(delay)
        
        await msg.edit(typed)
    except Exception as e:
        logger.error(f"Ошибка анимации: {e}")
        await event.edit("⚠️ Ошибка при выполнении")

async def tp_animation(event):
    """Альтернативная анимация печати"""
    try:
        input_str = event.text.split('.а', 1)[1].strip()
        if not input_str:
            await event.edit("ℹ️ Введите текст после .а")
            return

        typing_symbol = "<"
        previous_text = ""
        await event.edit(typing_symbol)
        
        for character in input_str:
            previous_text += character
            typing_text = previous_text + typing_symbol
            await event.edit(f'<b>{typing_text}</b>', parse_mode='html')
            await asyncio.sleep(0.1)
        
        await event.edit(previous_text)
    except Exception as e:
        logger.error(f"Ошибка анимации: {e}")
        await event.edit("⚠️ Ошибка при выполнении")

async def change_cursor(event):
    """Сменить курсор"""
    try:
        new_cursor = event.text.split('.s', 1)[1].strip()
        if not new_cursor:
            await event.edit("ℹ️ Укажите новый символ курсора")
            return

        user_id = str(event.sender_id)
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['cursor'] = new_cursor
        save_settings(user_settings)
        
        await event.edit(f"✅ Курсор изменен на: <code>{new_cursor}</code>", parse_mode='html')
    except Exception as e:
        logger.error(f"Ошибка смены курсора: {e}")
        await event.edit("⚠️ Ошибка при изменении курсора")

async def set_delay(event):
    """Изменить задержку"""
    try:
        delay_str = event.text.split('.t', 1)[1].strip()
        if not delay_str:
            await event.edit("ℹ️ Укажите задержку (например .t 0.1)")
            return

        new_delay = float(delay_str)
        user_id = str(event.sender_id)
        
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['delay'] = new_delay
        save_settings(user_settings)
        
        await event.edit(f"✅ Задержка изменена на: <code>{new_delay} сек</code>", parse_mode='html')
    except ValueError:
        await event.edit("⚠️ Задержка должна быть числом (например 0.1)")
    except Exception as e:
        logger.error(f"Ошибка установки задержки: {e}")
        await event.edit("⚠️ Ошибка при изменении задержки")

async def reset_settings(event):
    """Сбросить настройки"""
    try:
        user_id = str(event.sender_id)
        if user_id in user_settings:
            del user_settings[user_id]
            save_settings(user_settings)
            await event.edit("✅ Настройки сброшены к стандартным")
        else:
            await event.edit("ℹ️ У вас нет сохраненных настроек")
    except Exception as e:
        logger.error(f"Ошибка сброса настроек: {e}")
        await event.edit("⚠️ Ошибка при сбросе настроек")

def setup(bot):
    bot.register_command("п", type_animation, "Анимация печати текста", "Typing")
    bot.register_command("s", change_cursor, "Сменить курсор (.s ▯)", "Typing")
    bot.register_command("t", set_delay, "Изменить задержку (.t 0.1)", "Typing")
    bot.register_command("q", reset_settings, "Сбросить настройки", "Typing")
    bot.register_command("а", tp_animation, "Альтернативная анимация печати", "Typing")
    
    # Установка описания модуля
    bot.set_module_description("Typing", "Анимации набора текста и эффекты печати")