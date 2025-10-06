import os
from random import randrange

import dotenv
import vk_api
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll


def main():
    dotenv.load_dotenv()

    token = os.environ['TOKEN']

    vk = vk_api.VkApi(token=token)
    longpoll = VkLongPoll(vk)


    def write_msg(user_id, message):
        vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)})


    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            write_msg(event.user_id, f'Test: {event.text}')

if __name__ == '__main__':
    main()
