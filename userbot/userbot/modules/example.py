from telethon import events
import logging

logger = logging.getLogger("UserBot.Example")

async def send_emoji_message(event):
    """Отправляет тестовое сообщение с премиум-эмодзи"""
    try:
        message = (
            "привет [💢](emoji/5251522431977291010)\n\n"
            "Это тестовое сообщение с премиум-эмодзи!"
        )
        await event.edit(message)
    except Exception as e:
        logger.error(f"Ошибка отправки эмодзи: {str(e)}")
        await event.edit("⚠️ Не удалось отправить сообщение с эмодзи")

def setup(bot):
    bot.set_module_description(
        "Example", 
        "Демонстрация работы премиум-эмодзи"
    )
    bot.register_command(
        cmd="emoji_test",
        handler=send_emoji_message,
        description="Тест премиум-эмодзи",
        module_name="Example",
        aliases=["et", "тест_эмодзи"]
    )