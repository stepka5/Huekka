import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Настраивает систему логирования"""
    # Создаем папку для логов
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # Основной логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Фильтр для блокировки INFO от telethon.client.updates
    class TelethonUpdatesFilter(logging.Filter):
        def filter(self, record):
            if record.name == "telethon.client.updates" and record.levelno == logging.INFO:
                return False
            return True
    
    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(TelethonUpdatesFilter())  # Добавляем фильтр
    logger.addHandler(console_handler)
    
    # Файловый вывод (с ротацией)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "userbot.log"),
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(TelethonUpdatesFilter())  # Добавляем фильтр
    logger.addHandler(file_handler)
    
    # Устанавливаем уровень логирования для telethon.client.updates
    updates_logger = logging.getLogger("telethon.client.updates")
    updates_logger.setLevel(logging.ERROR)  # Только ERROR и выше
    
    return logger