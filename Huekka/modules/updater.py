# modules/Updater.py
import os
import sys
import asyncio
import logging
import shutil
import tempfile
import difflib
import hashlib
from pathlib import Path
import git
from telethon import events

logger = logging.getLogger("UserBot.Updater")

class UpdaterModule:
    def __init__(self, bot):
        self.bot = bot
        self.repo_url = "https://github.com/stepka5/Huekka"  # Замените на ваш репозиторий
        self.branch = "main"  # Или другая ветка
        self.exclude_dirs = ["session", "cash", "logs", "modules"]  # Папки, которые не обновляем
        self.exclude_files = ["config.py"]  # Файлы, которые не обновляем
        
        # ID эмодзи для статусов
        self.update_emoji_id = 5422360919453756368  # 🌘
        self.success_emoji_id = 5251481573953405172  # ▫️
        self.error_emoji_id = 5233732265120394046   # 🫶
        self.file_emoji_id = 5251522431977291010    # ℹ️
        
        bot.register_command(
            cmd="update",
            handler=self.update_bot,
            description="Обновить бота из GitHub репозитория",
            module_name="Updater",
            aliases=["upgrade"]
        )
        
        bot.set_module_description("Updater", "Система обновления бота через GitHub")

    async def get_user_info(self, event):
        """Получение информации о пользователе"""
        try:
            user = await event.get_sender()
            return {
                "premium": user.premium if hasattr(user, 'premium') else False,
                "username": user.username or f"id{user.id}"
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
            return {"premium": False, "username": "unknown"}

    def calculate_file_hash(self, file_path):
        """Вычисление SHA-256 хеша файла"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def should_update_file(self, src, dest):
        """Определяет, нужно ли обновлять файл"""
        if not os.path.exists(dest):
            return True
        
        # Сравниваем хеши файлов
        return self.calculate_file_hash(src) != self.calculate_file_hash(dest)

    async def format_update_message(self, changes, is_premium):
        """Форматирование сообщения об обновлении"""
        text = ""
        if is_premium:
            text += f"[🌘](emoji/{self.update_emoji_id}) "
        text += "**Обновление бота**\n\n"
        
        if changes["added"]:
            text += "**Добавлены файлы:**\n"
            text += "\n".join(f"▫️ `{file}`" for file in changes["added"]) + "\n\n"
        
        if changes["modified"]:
            text += "**Обновлены файлы:**\n"
            text += "\n".join(f"▫️ `{file}`" for file in changes["modified"]) + "\n\n"
        
        if changes["removed"]:
            text += "**Удалены файлы:**\n"
            text += "\n".join(f"▫️ `{file}`" for file in changes["removed"]) + "\n\n"
        
        if is_premium:
            text += f"[▫️](emoji/{self.success_emoji_id}) "
        text += "**Обновление завершено! Бот будет перезагружен.**"
        
        return text

    async def animate_updating(self, event, message, is_premium):
        """Анимация процесса обновления"""
        animation = ["⏳", "⌛", "⏳", "⌛"]
        start_time = asyncio.get_event_loop().time()
        i = 0
        
        try:
            while asyncio.get_event_loop().time() - start_time < 5:  # 5 секунд анимации
                frame = animation[i % len(animation)]
                prefix = f"[{frame}](emoji/{self.update_emoji_id}) " if is_premium else f"{frame} "
                await event.edit(f"{prefix}{message}")
                i += 1
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Ошибка анимации: {str(e)}")

    async def update_bot(self, event):
        """Обработчик команды .update"""
        user_info = await self.get_user_info(event)
        is_premium = user_info["premium"]
        
        # Запускаем анимацию
        anim_task = asyncio.create_task(
            self.animate_updating(event, "Обновление бота...", is_premium)
        )
        
        changes = {
            "added": [],
            "modified": [],
            "removed": []
        }
        
        try:
            # Создаем временную директорию для клонирования
            with tempfile.TemporaryDirectory() as temp_dir:
                # Клонируем репозиторий
                repo = git.Repo.clone_from(
                    self.repo_url,
                    temp_dir,
                    branch=self.branch,
                    depth=1
                )
                
                # Обходим файлы в репозитории
                for root, dirs, files in os.walk(temp_dir):
                    # Пропускаем исключенные директории
                    if any(ex_dir in root for ex_dir in self.exclude_dirs):
                        continue
                    
                    # Определяем относительный путь
                    rel_path = os.path.relpath(root, temp_dir)
                    dest_path = os.path.join(os.getcwd(), rel_path)
                    
                    # Создаем целевую директорию, если нужно
                    os.makedirs(dest_path, exist_ok=True)
                    
                    # Обрабатываем файлы
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_path, file)
                        
                        # Пропускаем исключенные файлы
                        if any(ex_file in dest_file for ex_file in self.exclude_files):
                            continue
                        
                        # Проверяем, нужно ли обновлять файл
                        if not os.path.exists(dest_file) or self.should_update_file(src_file, dest_file):
                            shutil.copy2(src_file, dest_file)
                            
                            if not os.path.exists(dest_file):
                                changes["added"].append(os.path.join(rel_path, file))
                            else:
                                changes["modified"].append(os.path.join(rel_path, file))
                
                # Проверяем удаленные файлы (сравнивая с текущей структурой)
                for root, dirs, files in os.walk(os.getcwd()):
                    # Пропускаем исключенные директории
                    if any(ex_dir in root for ex_dir in self.exclude_dirs):
                        continue
                    
                    rel_path = os.path.relpath(root, os.getcwd())
                    src_path = os.path.join(temp_dir, rel_path)
                    
                    for file in files:
                        src_file = os.path.join(src_path, file)
                        dest_file = os.path.join(root, file)
                        
                        # Пропускаем исключенные файлы
                        if any(ex_file in dest_file for ex_file in self.exclude_files):
                            continue
                        
                        # Если файл есть в текущей версии, но отсутствует в репозитории
                        if not os.path.exists(src_file):
                            changes["removed"].append(os.path.join(rel_path, file))
            
            # Форматируем сообщение об обновлении
            if changes["added"] or changes["modified"] or changes["removed"]:
                update_message = await self.format_update_message(changes, is_premium)
            else:
                update_message = "ℹ️ Обновлений не найдено. Бот уже актуален!"
            
            await event.edit(update_message)
            
            # Перезагружаем бота, если были изменения
            if changes["added"] or changes["modified"] or changes["removed"]:
                logger.info("Обновление завершено, перезагрузка бота...")
                await asyncio.sleep(2)
                await self.bot.restart()
                
        except git.exc.GitCommandError as e:
            error_msg = f"🚫 Ошибка Git: {str(e)}"
            logger.error(error_msg)
            await event.edit(error_msg)
        except Exception as e:
            error_msg = f"🚫 Критическая ошибка при обновлении: {str(e)}"
            logger.exception(error_msg)
            await event.edit(error_msg)
        finally:
            # Гарантируем завершение анимации
            if not anim_task.done():
                anim_task.cancel()

def setup(bot):
    UpdaterModule(bot)
