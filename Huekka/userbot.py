#ролффдлрдфрпофроуружРПУРОЛПРЖДРДЛрдРП
import os
import sys
import asyncio
import logging
import importlib.util
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from core.parser import CustomParseMode, EmojiHandler

# Импортируем нашу улучшенную систему логирования
from core.log import setup_logging  # <-- Добавленный импорт

# Настройка логов
logger = setup_logging()  # <-- Заменяем basicConfig на нашу функцию
logger = logging.getLogger("UserBot")  # <-- Сохраняем именованный логгер

class UserBot:
    def __init__(self):
        self.client = None
        self.modules = {}
        self.commands = {}
        self.cache_dir = "cash"
        self.module_descriptions = {}
        self.core_modules = ["Help", "System", "Loader"]
        self.post_restart_actions = []
        self.last_loaded_module = None
        
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs("modules", exist_ok=True)
        self._init_client()
    
    # ... остальной код без изменений ...
    def _init_client(self):
        """Инициализация клиента Telegram"""
        config_path = os.path.join("session", "config.py")
        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        self.client = TelegramClient(
            StringSession(config.Config.SESSION_STRING),
            config.Config.API_ID,
            config.Config.API_HASH
        )
        
        # Устанавливаем кастомный парсер Markdown
        self.client.parse_mode = CustomParseMode()
    
    async def start(self):
        """Запуск юзербота"""
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            logger.error("Ошибка авторизации! Проверьте сессию в session/config.py")
            return
        
        # Обработчик команд
        @self.client.on(events.NewMessage(outgoing=True, pattern=r'\.(\w+)(?:\s+([\s\S]*))?$'))
        async def command_handler(event):
            cmd = event.pattern_match.group(1).lower()
            args = event.pattern_match.group(2) or ""
            
            if cmd in self.commands:
                try:
                    event.text = f".{cmd} {args}"
                    await self.commands[cmd]["handler"](event)
                except Exception as e:
                    logger.error(f"Ошибка в команде .{cmd}: {str(e)}")
                    await event.edit(f"⚠️ Ошибка: {str(e)}")
        
        # Обработчик обычных сообщений для эмодзи
        @self.client.on(events.NewMessage(outgoing=True))
        async def message_handler(event):
            await EmojiHandler.process_message(event)
        
        await self.load_modules()
        
        for action in self.post_restart_actions:
            try:
                await action()
            except Exception as e:
                logger.error(f"Ошибка выполнения post-restart action: {str(e)}")
        self.post_restart_actions = []
        
        if self.last_loaded_module:
            module_name, chat_id, reply_to = self.last_loaded_module
            try:
                if "help" in self.commands:
                    event = events.NewMessage.Event(
                        message=events.Message(
                            id=0,
                            peer=await self.client.get_input_entity(chat_id),
                            text=f".help {module_name}",
                            reply_to=reply_to
                        )
                    )
                    await self.commands["help"]["handler"](event)
            except Exception as e:
                logger.error(f"Ошибка при автоматическом показе справки: {str(e)}")
            finally:
                self.last_loaded_module = None
        
        me = await self.client.get_me()
        logger.info(f"Бот запущен как @{me.username} (ID: {me.id})")
        await self.client.run_until_disconnected()

    async def load_modules(self):
        """Загрузка модулей"""
        modules_dir = "modules"
        for file in os.listdir(modules_dir):
            if file.endswith(".py") and file != "__init__.py":
                try:
                    module_path = os.path.join(modules_dir, file)
                    module_name = file[:-3]
                    
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'setup'):
                        before = len(self.commands)
                        module.setup(self)
                        after = len(self.commands)
                        logger.info(f"Модуль {module_name} загружен (команд: {after - before})")
                except Exception as e:
                    logger.error(f"Ошибка загрузки модуля {file}: {str(e)}")

    def register_command(self, cmd, handler, description="", module_name="System", aliases=None):
        """Регистрация команды"""
        aliases = aliases or []
        self.commands[cmd] = {
            "handler": handler,
            "description": description,
            "module": module_name,
            "aliases": aliases
        }
        
        for alias in aliases:
            self.commands[alias] = {
                "handler": handler,
                "description": description,
                "module": module_name,
                "is_alias": True
            }
        
        if module_name not in self.modules:
            self.modules[module_name] = {}
        
        self.modules[module_name][cmd] = {
            "description": description,
            "aliases": aliases
        }
    
    def set_module_description(self, module_name, description):
        self.module_descriptions[module_name] = description
    
    def add_post_restart_action(self, action):
        self.post_restart_actions.append(action)
    
    async def restart(self):
        logger.info("Перезагрузка бота...")
        os.execl(sys.executable, sys.executable, *sys.argv)

async def main():
    bot = UserBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
