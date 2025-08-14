import os
import sys
import importlib
import asyncio
import logging
import sqlite3
from pathlib import Path
from telethon import events, types
from telethon.errors import MessageNotModifiedError
import traceback
import time

logger = logging.getLogger("UserBot.Loader")

class LoaderModule:
    def __init__(self, bot):
        self.bot = bot
        
        # ID эмодзи для разных статусов
        self.loader_emoji_id = 4904936030232117798  # ⚙️
        self.loaded_emoji_id = 5422360919453756368  # 🌘
        self.command_emoji_id = 5251481573953405172  # ▫️
        self.dev_emoji_id = 5233732265120394046     # 🫶
        self.info_emoji_id = 5251522431977291010    # ℹ️
        
        bot.register_command(
            cmd="lm",
            handler=self.load_module,
            description="Загрузить модуль из файла",
            module_name="Loader"
        )
        
        bot.register_command(
            cmd="ulm",
            handler=self.unload_module,
            description="Выгрузить модуль",
            module_name="Loader",
            aliases=["unload"]
        )
        
        bot.set_module_description("Loader", "Динамическая загрузка модулей")
        
        # Подключаемся к базе смайликов
        self.smile_db_path = Path("cash") / "smiles.db"
        self._init_smile_database()

    def _init_smile_database(self):
        """Инициализация базы смайлов (если не существует)"""
        os.makedirs("cash", exist_ok=True)
        conn = sqlite3.connect(self.smile_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS smiles
                     (id INTEGER PRIMARY KEY, smile TEXT)''')
        if c.execute("SELECT COUNT(*) FROM smiles").fetchone()[0] == 0:
            smiles = ["╰(^∇^)╯", "(〜￣▽￣)〜", "٩(◕‿◕｡)۶", "ヾ(＾-＾)ノ", 
                     "ʕ•́ᴥ•̀ʔっ", "(◠‿◠✿)", "(◕ω◕✿)", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", 
                     "♡(˃͈ દ ˂͈ ༶ )", "ヽ(♡‿♡)ノ"]
            for smile in smiles:
                c.execute("INSERT INTO smiles (smile) VALUES (?)", (smile,))
            conn.commit()
        conn.close()

    def get_random_smile(self):
        """Получение случайного смайла"""
        conn = sqlite3.connect(self.smile_db_path)
        smile = conn.cursor().execute(
            "SELECT smile FROM smiles ORDER BY RANDOM() LIMIT 1"
        ).fetchone()[0]
        conn.close()
        return smile

    async def get_user_info(self, event):
        """Получение информации о пользователе с кэшированием"""
        try:
            user = await event.get_sender()
            return {
                "premium": user.premium if hasattr(user, 'premium') else False,
                "username": user.username or f"id{user.id}"
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
            return {"premium": False, "username": "unknown"}

    async def find_module_info(self, module_name):
        """
        Находит информацию о модуле по имени файла или имени регистрации
        Возвращает кортеж: (найденное имя модуля, информация)
        """
        # Прямое совпадение
        if module_name in self.bot.modules:
            return module_name, await self.get_module_info(module_name)
        
        # Поиск без учета регистра
        for name in self.bot.modules.keys():
            if name.lower() == module_name.lower():
                return name, await self.get_module_info(name)
        
        # Поиск по имени файла без расширения
        file_name = module_name.lower().replace('.py', '')
        for name in self.bot.modules.keys():
            if name.lower() == file_name:
                return name, await self.get_module_info(name)
        
        return None, None

    async def get_module_info(self, module_name):
        """Получение информации о модуле"""
        if module_name not in self.bot.modules:
            return None
            
        commands = []
        for cmd, data in self.bot.modules[module_name].items():
            # Пропускаем алиасы
            if data.get("is_alias", False):
                continue
                
            commands.append({
                "command": cmd,
                "description": data.get("description", "Без описания"),
                "aliases": data.get("aliases", [])
            })
        
        return {
            "name": module_name,
            "description": self.bot.module_descriptions.get(module_name, ""),
            "commands": commands,
            "is_stock": module_name in self.bot.core_modules,
            "version": "1.0.0",
            "developer": "@username"
        }

    async def format_module_loaded_message(self, module_info, event):
        """Форматирование сообщения о загруженном модуле"""
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]
        
        text = ""
        if is_premium:
            text += f"[🌘](emoji/{self.loaded_emoji_id}) "
        text += f"**{module_info['name']} загружен (v{module_info['version']})**\n"
        
        if module_info['description']:
            text += f"__{module_info['description']}__\n"
            
        text += f"__{self.get_random_smile()}__\n\n"
        
        for cmd in module_info['commands']:
            if is_premium:
                text += f"[▫️](emoji/{self.command_emoji_id}) "
            else:
                text += "▫️ "
                
            # Добавляем точку перед командой
            text += f"`.{cmd['command']}`"
            
            if cmd['aliases']:
                text += f" ({' | '.join([f'`.{alias}`' for alias in cmd['aliases']])})"
            
            text += f" - __{cmd['description']}__\n"
        
        text += "\n"
        if is_premium:
            text += f"[🫶](emoji/{self.dev_emoji_id}) "
        else:
            text += "🫶 "
        text += f"**Разработчик:** {module_info['developer']}"
        
        return text

    async def format_module_unloaded_message(self, module_name, event):
        """Форматирование сообщения об удалении модуля"""
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]
        
        text = ""
        if is_premium:
            text += f"[ℹ️](emoji/{self.info_emoji_id})"
        else:
            text += "ℹ️"
        
        text += f"**Модуль {module_name} успешно удален.**\n"
        text += f"__(Используйте .help для просмотра модулей и команд.)__"
        
        return text

    async def animate_loading(self, event, message, is_premium):
        """Анимация загрузки/выгрузки с минимальным временем показа"""
        animation = ["/", "-", "\\", "|"]
        start_time = time.time()
        i = 0
        
        # Минимальное время показа анимации (2 секунды)
        min_duration = 2.0
        
        try:
            while time.time() - start_time < min_duration:
                frame = animation[i % len(animation)]
                prefix = f"[⚙️](emoji/{self.loader_emoji_id}) " if is_premium else "⚙️ "
                await event.edit(f"{prefix}{message} {frame}")
                i += 1
                await asyncio.sleep(0.3)  # Быстрее обновление
        except MessageNotModifiedError:
            pass
        except Exception as e:
            logger.error(f"Ошибка анимации: {str(e)}")

    async def load_module(self, event):
        """Обработчик команды .lm"""
        if not event.is_reply:
            await event.edit("ℹ️ Ответьте на сообщение с файлом модуля!")
            return

        reply = await event.get_reply_message()
        if not reply.document or not reply.document.mime_type == "text/x-python":
            await event.edit("⚠️ Это не Python-файл!")
            return

        # Получаем информацию о пользователе
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        # Скачиваем файл модуля
        module_file = await reply.download_media(file="modules/")
        module_name = os.path.basename(module_file).replace(".py", "")
        
        # Запускаем анимацию
        anim_task = asyncio.create_task(
            self.animate_loading(event, f"Загружаю модуль `{module_name}`", is_premium)
        )

        try:
            # Начинаем загрузку
            start_time = time.time()
            
            # Сохраняем текущее состояние команд
            before_commands = set(self.bot.commands.keys())
            
            # Динамическая загрузка модуля
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'setup'):
                module.setup(self.bot)
                
                # Находим новые команды
                after_commands = set(self.bot.commands.keys())
                new_commands = after_commands - before_commands
                
                # Пытаемся найти имя модуля
                found_name, module_info = await self.find_module_info(module_name)
                
                # Гарантируем минимальное время анимации
                elapsed = time.time() - start_time
                if elapsed < 2.0:
                    await asyncio.sleep(2.0 - elapsed)
                
                if module_info:
                    # Форматируем сообщение о загрузке
                    loaded_message = await self.format_module_loaded_message(module_info, event)
                    await event.edit(loaded_message)
                    logger.info(f"Модуль {found_name} загружен (команд: {len(new_commands)})")
                else:
                    # Резервное создание информации
                    module_info = {
                        "name": module_name,
                        "description": "Описание недоступно",
                        "commands": [{
                            "command": cmd, 
                            "description": self.bot.commands[cmd].get("description", "Без описания"), 
                            "aliases": []
                        } for cmd in new_commands],
                        "version": "1.0.0",
                        "developer": "@username"
                    }
                    loaded_message = await self.format_module_loaded_message(module_info, event)
                    await event.edit(loaded_message)
            else:
                await event.edit(f"⚠️ В модуле отсутствует функция setup()!")
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка загрузки модуля: {str(e)}\n{error_trace}")
            await event.edit(
                f"🚫 Ошибка загрузки модуля: ```{str(e)}```\n"
                "ℹ️ Проверьте логи для подробностей."
            )
        finally:
            # Гарантируем завершение анимации
            if not anim_task.done():
                anim_task.cancel()

    async def unload_module(self, event):
        """Обработчик команды .ulm"""
        args = event.text.split()
        if len(args) < 2:
            await event.edit("ℹ️ Укажите название модуля: `.ulm ModuleName`")
            return

        module_name = args[1].strip()
        module_path = f"modules/{module_name}.py"
        
        # Проверяем существует ли модуль
        if not os.path.exists(module_path):
            await event.edit(f"⚠️ Модуль `{module_name}` не найден!")
            return
            
        # Пытаемся найти реальное имя модуля
        found_name, module_info = await self.find_module_info(module_name)
        if not found_name:
            await event.edit(f"⚠️ Модуль `{module_name}` не загружен!")
            return

        # Получаем информацию о пользователе
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]

        # Запускаем анимацию
        anim_task = asyncio.create_task(
            self.animate_loading(event, f"Удаляю модуль `{found_name}`", is_premium)
        )

        try:
            # Начинаем удаление
            start_time = time.time()
            
            # Удаляем команды модуля
            commands_to_remove = [
                cmd for cmd, data in self.bot.commands.items() 
                if data.get("module") and data.get("module").lower() == found_name.lower()
            ]
            
            for cmd in commands_to_remove:
                del self.bot.commands[cmd]
            
            # Удаляем из системных модулей
            if found_name in sys.modules:
                del sys.modules[found_name]
            
            # Удаляем файл
            os.remove(module_path)
            
            # Удаляем из описания
            if found_name in self.bot.modules:
                del self.bot.modules[found_name]
            
            if found_name in self.bot.module_descriptions:
                del self.bot.module_descriptions[found_name]
            
            # Гарантируем минимальное время анимации
            elapsed = time.time() - start_time
            if elapsed < 2.0:
                await asyncio.sleep(2.0 - elapsed)
            
            # Форматируем сообщение об удалении
            unloaded_message = await self.format_module_unloaded_message(found_name, event)
            message = await event.edit(unloaded_message)
            
            # Удаляем сообщение через 50 секунд
            await asyncio.sleep(50)
            await message.delete()
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Ошибка выгрузки модуля: {str(e)}\n{error_trace}")
            await event.edit(
                f"🚫 Ошибка выгрузки модуля: ```{str(e)}```\n"
                "ℹ️ Проверьте логи для подробностей."
            )
        finally:
            # Гарантируем завершение анимации
            if not anim_task.done():
                anim_task.cancel()

def setup(bot):
    LoaderModule(bot)