import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app_bot.search_bot import Search_BOT


def main():
    bot = Search_BOT()
    bot.start()

if __name__ == '__main__':
    main()