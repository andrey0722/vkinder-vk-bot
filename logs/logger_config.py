"""
Модуль для настройки системы логирования бота.

Этот модуль создает и настраивает логгер, который:
- Записывает логи в файл logs/bot.log
- Выводит логи в консоль
- Автоматически создает папку logs, если её нет
"""

import logging
import sys
from pathlib import Path
from time import asctime
import colorlog


def setup_logger(name='vk_bot', log_level=logging.INFO):
    """
    Создает и настраивает логгер для приложения.
    
    Args:
        name (str): Имя логгера (по умолчанию 'vk_bot')
        log_level: Уровень логирования (по умолчанию INFO)
        
    Returns:
        logging.Logger: Настроенный объект логгера
        
    Пример использования:
        logger = setup_logger()
        logger.info("Привет, мир!")
    """


    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)


    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        # %(asctime)s - время события в формате "2025-10-07 15:30:45"
        # %(name)s - имя логгера (vk_bot)
        # %(levelname)-8s - уровень лога (INFO, ERROR и т.д.), -8s = выравнивание по 8 символов
        # %(funcName)s - имя функции, которая вызвала лог
        # %(lineno)d - номер строки, где вызван лог
        # %(message)s - само сообщение 

        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s | %(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        
    )

    console_formatter = colorlog.ColoredFormatter(
        fmt='%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s | %(cyan)s%(funcName)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'white',        # Белый
            'INFO': 'green',         # Зелёный
            'WARNING': 'yellow',     # Жёлтый
            'ERROR': 'red',          # Красный
            'CRITICAL': 'red,bg_white',  # Красный текст на белом фоне
        },
    )

    file_handler = logging.FileHandler(
        filename=log_dir/'bot_log',
        mode='a',
        encoding='utf-8',
    )

    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(
        stream=sys.stdout
    )

    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False
    
    return logger

def get_logger(name=None):
    """
    Быстрый способ получить логгер в любом модуле.
    
    Args:
        name (str): Имя модуля (обычно используют __name__)
        
    Returns:
        logging.Logger: Объект логгера
        
    Пример:
        from logger_config import get_logger
        logger = get_logger(__name__)
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger('vk_bot')


# ========== ТЕСТИРОВАНИЕ (запускается только при прямом запуске файла) ==========
if __name__ == '__main__':
    # Это блок для тестирования логгера
    # Выполнится только если запустить: python logger_config.py
    
    print("=== Тестирование логгера ===\n")
    
    # Создаем тестовый логгер
    test_logger = setup_logger()
    
    # Тестируем все уровни логирования
    test_logger.debug("Это DEBUG сообщение - для детальной отладки")
    test_logger.info("Это INFO сообщение - обычная информация")
    test_logger.warning("Это WARNING - предупреждение о потенциальной проблеме")
    test_logger.error("Это ERROR - произошла ошибка")
    test_logger.critical("Это CRITICAL - критическая ошибка!")
    
    print("\n✅ Логи записаны в файл logs/bot.log")
    print("✅ Логи выведены в консоль")