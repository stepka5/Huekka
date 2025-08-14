import os
import sys
import asyncio
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
    PhoneCodeInvalidError
)

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Папка для сессий
SESSION_DIR = "session"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

async def setup_session():
    print("\n" + Colors.OKCYAN + "="*50 + Colors.ENDC)
    print(Colors.HEADER + "   ⚡ Настройка UserBot   " + Colors.ENDC)
    print(Colors.OKCYAN + "="*50 + Colors.ENDC)
    
    api_id = input(Colors.BOLD + "[?] Введите API_ID: " + Colors.ENDC).strip()
    api_hash = input(Colors.BOLD + "[?] Введите API_HASH: " + Colors.ENDC).strip()
    phone = input(Colors.BOLD + "[?] Введите номер телефона: " + Colors.ENDC).strip()
    
    phone_clean = ''.join(filter(str.isdigit, phone))
    if len(phone_clean) < 10:
        print(Colors.FAIL + "❌ Неверный формат номера!" + Colors.ENDC)
        return
        
    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.connect()
    
    await client.send_code_request(phone_clean)
    print(Colors.OKGREEN + f"\n📲 Код подтверждения отправлен на {phone_clean}" + Colors.ENDC)
    
    code_attempts = 0
    while code_attempts < 3:
        code = input(Colors.BOLD + "[?] Введите код из SMS: " + Colors.ENDC).replace('-', '')
        
        try:
            await client.sign_in(phone_clean, code=code)
            break
        except SessionPasswordNeededError:
            password = input(Colors.BOLD + "[?] Введите пароль 2FA: " + Colors.ENDC)
            try:
                await client.sign_in(password=password)
                break
            except Exception as e:
                print(Colors.FAIL + f"❌ Ошибка входа: {str(e)}" + Colors.ENDC)
                code_attempts = 3
        except Exception as e:
            print(Colors.FAIL + f"❌ Ошибка входа: {str(e)}" + Colors.ENDC)
            code_attempts += 1
    
    if code_attempts >= 3:
        print(Colors.FAIL + "🚫 Слишком много неудачных попыток" + Colors.ENDC)
        return
        
    session_str = client.session.save()
    
    # Создаем config.py в папке session
    config_path = os.path.join(SESSION_DIR, "config.py")
    with open(config_path, "w") as f:
        f.write(f"class Config:\n")
        f.write(f"    API_ID = {api_id}\n")
        f.write(f"    API_HASH = '{api_hash}'\n")
        f.write(f"    SESSION_STRING = '{session_str}'\n")
    
    print(Colors.OKGREEN + f"✅ Конфигурация сохранена в {config_path}" + Colors.ENDC)
    print(Colors.OKGREEN + "✅ Запускаю бота..." + Colors.ENDC)
    
    os.system(f"{sys.executable} userbot.py")

if __name__ == "__main__":
    config_path = os.path.join(SESSION_DIR, "config.py")
    if not os.path.exists(config_path):
        asyncio.run(setup_session())
    else:
        print(Colors.OKGREEN + "✅ Конфигурация найдена, запускаю бота..." + Colors.ENDC)
        os.system(f"{sys.executable} userbot.py")