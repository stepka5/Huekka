from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

class EmojiMarkerModule:
    def __init__(self, bot):
        self.bot = bot
        bot.register_command(
            cmd="dd",
            handler=self.get_emoji_marker,
            description="Получить маркер для премиум-эмодзи",
            module_name="Emoji",
            aliases=["d", "эмодзи"]
        )

    async def get_emoji_marker(self, event):
        """Получает маркер для премиум-эмодзи из ответного сообщения"""
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("❌ Ответьте на сообщение с премиум-эмодзи!")
            return
            
        if not reply.entities:
            await event.edit("❌ В сообщении нет премиум-эмодзи!")
            return
            
        # Ищем кастомные эмодзи
        custom_emojis = []
        for entity in reply.entities:
            if isinstance(entity, MessageEntityCustomEmoji):
                emoji_char = reply.message[entity.offset:entity.offset + entity.length]
                custom_emojis.append((emoji_char, entity.document_id))
        
        if not custom_emojis:
            await event.edit("❌ В сообщении нет премиум-эмодзи!")
            return
            
        # Формируем результат
        result = "✨ Готовые маркеры для вашего эмодзи:\n\n"
        for i, (emoji_char, doc_id) in enumerate(custom_emojis, 1):
            result += f"{i}. `[{emoji_char}](emoji/{doc_id})`\n"
            result += f"   Код для вставки: `<emoji document_id={doc_id}>{emoji_char}</emoji>`\n\n"
        
        result += "📝 Используйте первый формат для сообщений, второй для XML-тегов"
        
        await event.edit(result, parse_mode="markdown")

def setup(bot):
    bot.set_module_description("EmojiMarker", "Генератор маркеров для премиум-эмодзи")
    EmojiMarkerModule(bot)