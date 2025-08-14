import logging
import difflib
import random
import sqlite3
import os
from telethon import events
from pathlib import Path

logger = logging.getLogger("UserBot.Help")

class HelpModule:
    def __init__(self, bot):
        self.bot = bot
        self.stock_modules = ["Help", "System", "Loader"]
        
        # ID премиум-эмодзи
        self.total_emoji_id = 5422360919453756368  # 🌘
        self.section_emoji_id = 5377520790868603876  # ▪️
        self.stock_emoji_id = 5251522431977291010  # ▪️
        self.custom_emoji_id = 5251481573953405172  # ▫️
        self.developer_emoji_id = 5233732265120394046  # 🫶
        
        self.smile_db_path = Path("cash") / "smiles.db"
        self._init_smile_database()
        
        bot.register_command(
            cmd="help",
            handler=self.show_help,
            description="Показать список команд",
            module_name="Help",
            aliases=["h", "помощь"]
        )
    
    def _init_smile_database(self):
        os.makedirs("cash", exist_ok=True)
        conn = sqlite3.connect(self.smile_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS smiles
                     (id INTEGER PRIMARY KEY, smile TEXT)''')
        if c.execute("SELECT COUNT(*) FROM smiles").fetchone()[0] == 0:
            smiles = ["（〜^∇^ )〜", "〜(￣▽￣〜)", "(◕‿◕✿)", "ヽ(^o^)ノ", 
                     "╰(^∇^)╯", "(づ￣ ³￣)づ", "〜(￣▽￣〜)", "(〜￣▽￣)〜", 
                     "ヽ(^∇^)ﾉ", "╮(^▽^)╭"]
            for smile in smiles:
                c.execute("INSERT INTO smiles (smile) VALUES (?)", (smile,))
            conn.commit()
        conn.close()
    
    def get_random_smile(self):
        conn = sqlite3.connect(self.smile_db_path)
        smile = conn.cursor().execute("SELECT smile FROM smiles ORDER BY RANDOM() LIMIT 1").fetchone()[0]
        conn.close()
        return smile

    async def get_module_info(self, module_name):
        if module_name not in self.bot.modules:
            return None
            
        commands = []
        for cmd, data in self.bot.modules[module_name].items():
            commands.append({
                "command": cmd,
                "description": data.get("description", "Без описания"),
                "aliases": data.get("aliases", [])
            })
        
        return {
            "name": module_name,
            "description": self.bot.module_descriptions.get(module_name, ""),
            "commands": commands,
            "is_stock": module_name in self.stock_modules,
            "version": "1.0.0",
            "developer": "@username"
        }

    async def show_help(self, event):
        try:
            user = await event.get_sender()
            is_premium = user.premium if hasattr(user, 'premium') else False
        except Exception as e:
            logger.error(f"Ошибка проверки премиум-статуса: {str(e)}")
            is_premium = False
        
        args = event.text.split()
        
        if len(args) > 1:
            # Вывод конкретного модуля
            module_name = args[1].strip()
            module_info = await self.get_module_info(module_name)
            
            if not module_info:
                closest = difflib.get_close_matches(module_name, self.bot.modules.keys(), n=1, cutoff=0.6)
                if closest:
                    module_info = await self.get_module_info(closest[0])
            
            if not module_info:
                await event.edit(f"❌ Модуль `{module_name}` не найден")
                return
            
            # Форматируем название модуля
            text = ""
            if is_premium:
                text += f"[🌘](emoji/{self.total_emoji_id}) "
            text += f"**{module_info['name']} (v{module_info['version']})**\n"
            text += f"__{self.get_random_smile()}__\n\n"
            
            # Форматируем команды с моноширинным шрифтом
            for cmd in module_info['commands']:
                if is_premium:
                    if module_info['is_stock']:
                        text += f"[▪️](emoji/{self.stock_emoji_id}) "
                    else:
                        text += f"[▫️](emoji/{self.custom_emoji_id}) "
                else:
                    text += "▪️ " if module_info['is_stock'] else "▫️ "
                
                text += f"`.{cmd['command']}`"
                
                if cmd['aliases']:
                    text += f" ({' | '.join([f'`{alias}`' for alias in cmd['aliases']])})"
                
                text += f" - __{cmd['description']}__\n"
            
            # Форматируем разработчика
            if is_premium:
                text += f"\n[🫶](emoji/{self.developer_emoji_id}) "
            else:
                text += "\n🫶 "
            text += f"**Разработчик:** {module_info['developer']}"
            
            await event.edit(text)
            return

        # Общий список модулей
        total_modules = len(self.bot.modules)
        reply = ""
        
        if is_premium:
            reply += f"[🌘](emoji/{self.total_emoji_id}) "
        reply += f"**Доступно модулей:** {total_modules}\n"
        reply += "__Используйте .help <название> для подробной информации__\n\n"
        
        # Форматируем стоковые модули с моноширинными командами
        if is_premium:
            reply += f"[▪️](emoji/{self.section_emoji_id}) "
        reply += "**Стоковые модули:**\n"
        
        stock_list = []
        for module_name in self.stock_modules:
            if module_name not in self.bot.modules:
                continue
                
            if is_premium:
                stock_list.append(f"[▪️](emoji/{self.stock_emoji_id}) **{module_name}**: ( {' | '.join([f'`.{cmd}`' for cmd in self.bot.modules[module_name].keys()])} )")
            else:
                stock_list.append(f"▪️ **{module_name}**: ( {' | '.join([f'`.{cmd}`' for cmd in self.bot.modules[module_name].keys()])} )")
        
        reply += "\n".join(stock_list) + "\n\n"
        
        # Форматируем кастомные модули с моноширинными командами
        if is_premium:
            reply += f"[▪️](emoji/{self.section_emoji_id}) "
        reply += "**Кастомные модули:**\n"
        
        custom_list = []
        for module_name, commands in self.bot.modules.items():
            if module_name in self.stock_modules:
                continue
                
            if is_premium:
                custom_list.append(f"[▫️](emoji/{self.custom_emoji_id}) **{module_name}**: ( {' | '.join([f'`.{cmd}`' for cmd in commands.keys()])} )")
            else:
                custom_list.append(f"▫️ **{module_name}**: ( {' | '.join([f'`.{cmd}`' for cmd in commands.keys()])} )")
        
        reply += "\n".join(custom_list)
        
        await event.edit(reply)

def setup(bot):
    bot.set_module_description("Help", "Система помощи и информации о модулях")
    HelpModule(bot)