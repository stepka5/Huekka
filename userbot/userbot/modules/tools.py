import asyncio
import random
import logging
import time
from telethon import functions

logger = logging.getLogger(__name__)

async def zaeb_mention(event):
    """Заебать пользователя упоминаниями"""
    try:
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await event.edit("<b>❌ ответьте на сообщение!</b>", parse_mode='html')
            return
        
        await event.delete()
        for _ in range(70):
            msg = await event.respond(f'<a href="tg://user?id={reply.sender_id}">ебем мозги🧨</a>', parse_mode='html')
            await asyncio.sleep(random.uniform(0.3, 1.0))
            await msg.delete()
            await asyncio.sleep(0.5)

    except Exception as e:
        logger.error(f"ошибка в zaeb: {e}")

async def ping_cmd(event):
    """Проверить пинг бота"""
    start = time.time()
    msg = await event.edit("🏓 пинг...")
    await msg.edit(f"🏓 понг! {round((time.time()-start)*1000)}мс")

async def del_cmd(event):
    """Удалить сообщения до реплая"""
    if not event.reply_to_msg_id:
        await event.edit("⚠️ нужен реплай")
        return
        
    await event.edit("🧹 удаление...")
    msg_ids = []
    async for msg in event.client.iter_messages(event.chat_id, min_id=event.reply_to_msg_id):
        msg_ids.append(msg.id)
        if len(msg_ids) == 100:
            await event.client.delete_messages(event.chat_id, msg_ids)
            msg_ids = []
    if msg_ids:
        await event.client.delete_messages(event.chat_id, msg_ids)
    await event.delete()

async def report_user(event):
    """Устрашающий репорт с визуализацией ботнета"""
    try:
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("⚠️ Нужно ответить на сообщение пользователя!")
            return

        # Начало визуализации
        msg = await event.edit("🚀 Запускаю систему доносов...")
        
        # Этап 1: Активация ботнета
        botnet_size = random.randint(500, 1500)
        await asyncio.sleep(1)
        await msg.edit(
            f"🛰️ <b>Система доносов активирована!</b>\n"
            f"🔗 Подключено сессий: {botnet_size}\n"
            f"🔍 Сканирую профиль цели...", 
            parse_mode='html'
        )
        
        # Этап 2: Поиск нарушений
        violations = random.randint(3, 12)
        await asyncio.sleep(2)
        await msg.edit(
            f"🚨 <b>НАРУШЕНИЯ ОБНАРУЖЕНЫ!</b>\n"
            f"🔞 Запрещённый контент: {random.randint(1, violations)}\n"
            f"💢 Оскорбления: {random.randint(1, violations)}\n"
            f"⚠️ Спам: {random.randint(1, violations)}\n"
            f"🕵️‍♂️ Всего нарушений: {violations}",
            parse_mode='html'
        )
        
        # Этап 3: Формирование доноса
        await asyncio.sleep(2)
        await msg.edit(
            "📡 <b>Формирую донос в поддержку Telegram...</b>\n"
            "🖥️ Подключаю резервные сервера...",
            parse_mode='html'
        )
        
        # Анимация загрузки
        for i in range(1, 11):
            progress = "🟢" * i + "⚫️" * (10 - i)
            await msg.edit(
                f"📥 <b>Отправка доноса...</b>\n"
                f"⏳ Прогресс: {i*10}%\n"
                f"{progress}\n"
                f"🌐 Использовано сессий: {random.randint(50, 200)}",
                parse_mode='html'
            )
            await asyncio.sleep(0.3)
        
        # Финальный результат
        report_id = ''.join(random.choices('ABCDEF0123456789', k=16))
        await asyncio.sleep(1)
        await msg.edit(
            f"✅ <b>Донос успешно отправлен!</b>\n"
            f"🆔 ID доноса: <code>{report_id}</code>\n"
            f"⏱️ Время обработки: {random.uniform(3.7, 8.2):.1f} сек.\n"
            f"📊 Доносы за сегодня: {random.randint(15, 42)}\n\n"
            f"⚠️ Аккаунт будет проверен поддержкой в течение 24 часов",
            parse_mode='html'
        )

    except Exception as e:
        logger.error(f"Ошибка в report: {e}")
        await event.edit("⚠️ Произошла ошибка при формировании доноса")

def setup(bot):
    """Регистрация команд модуля"""
    bot.register_command("zaeb", zaeb_mention, "Заебать пользователя упоминаниями", "Tools")
    bot.register_command("ping", ping_cmd, "Проверить пинг бота", "Tools")
    bot.register_command("del", del_cmd, "Удалить сообщения до реплая", "Tools")
    bot.register_command("report", report_user, "Сформировать донос в поддержку Telegram", "Tools")
    
    # Установка описания модуля
    bot.set_module_description("Tools", "Полезные утилиты и инструменты")