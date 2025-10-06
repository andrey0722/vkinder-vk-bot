from typing import cast

from vkinder.config import Config
from vkinder.log import get_logger
from vkinder.log import setup_loging
from vkinder.vk import Vk


def main():
    setup_loging()
    logger = get_logger(main)

    logger.info('Started')

    config = Config()
    vk = Vk(config.vk_token)

    for event in vk.listen_messages():
        vk.send(f'Test: {event.text}', cast(int, event.user_id))


if __name__ == '__main__':
    main()
