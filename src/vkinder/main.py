from random import randrange

import vk_api
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll

from vkinder.config import Config
from vkinder.log import get_logger
from vkinder.log import setup_loging


def main():
    setup_loging()
    logger = get_logger(main)

    logger.info('Started')

    config = Config()
    vk = vk_api.VkApi(token=config.vk_token)
    longpoll = VkLongPoll(vk)


    def write_msg(user_id, message):
        logger.info('Sending message: %s, user: %s', message, event.user_id)
        vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)})


    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            logger.info('Got message: %s, user: %s', event.text, event.user_id)
            write_msg(event.user_id, f'Test: {event.text}')

if __name__ == '__main__':
    main()
