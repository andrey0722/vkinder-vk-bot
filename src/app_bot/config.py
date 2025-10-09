import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    VK_TOKEN_GROUP = os.getenv("TOKEN")
    if not VK_TOKEN_GROUP:
        raise ValueError("Токен не найден")
        
    VK_TOKEN_USER = os.getenv('TOKEN2')
    if not VK_TOKEN_USER:
        raise ValueError("Токен пользоваетля не найден")

    BOT_NAME = "Бот для знакомств"


config = Config()
