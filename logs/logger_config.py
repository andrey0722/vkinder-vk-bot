
import logging
import sys
from pathlib import Path
from time import asctime
import colorlog


def setup_logger(name='vk_bot', log_level=logging.INFO):

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)


    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(

        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s | %(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        
    )

    console_formatter = colorlog.ColoredFormatter(
        fmt='%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s | %(cyan)s%(funcName)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'white',      
            'INFO': 'green',         
            'WARNING': 'yellow',    
            'ERROR': 'red',          
            'CRITICAL': 'red,bg_white', 
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
    if name:
        return logging.getLogger(name)
    return logging.getLogger('vk_bot')

