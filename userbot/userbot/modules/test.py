from telethon import events

async def emoji_test(event):
    """Тест премиум-эмодзи"""
    message = (
        "**Тест премиум-эмодзи:**\n\n"
        "[▫️](emoji/5426861461064415727) - Обычный модуль\n"
        "[▪️](emoji/5274011327415730204) - Системный модуль\n\n"
        "_Проверка работы системы_"
    )
    await event.edit(message)

def setup(bot):
    bot.set_module_description("EmojiTest", "Тестирование премиум-эмодзи")
    bot.register_command(
        cmd="emojites11t",
        handler=emoji_test,
        description="Проверка работы премиум-эмодзи",
        module_name="EmojiTest"
    )