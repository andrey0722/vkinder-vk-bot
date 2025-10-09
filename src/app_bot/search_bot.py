from random import randrange, randint
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from app_bot.config import config
from logs.logger_config import setup_logger
import json


class Search_BOT:

    def __init__(self) -> None:

        self.logger = setup_logger("vk_bot")
        self.logger.info("=== Инициализация бота ===")
        try:
            self.group_token = config.VK_TOKEN_GROUP
            self.vk = vk_api.VkApi(token=self.group_token)
            self.longpoll = VkLongPoll(self.vk)
            self.bot_name = config.BOT_NAME

            # Токен пользователя
            self.user_token = config.VK_TOKEN_USER
            self.vk_user = vk_api.VkApi(token=self.user_token)

            self.logger.info("Бот успешно инициализирован")

        except Exception as e:
            self.logger.critical(f"Ошибка при инициализации: {e}", exc_info=True)
            raise

    def send_start_keyboard(self, user_id):
        self.logger.debug(f"Отправка клавиатуры пользователю {user_id}")
        try:
            keyboard = {
                "one_time": False,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "🔍 Поиск",
                            },
                            "color": "primary",
                        },
                        {
                            "action": {
                                "type": "text",
                                "label": "👤 Профиль",
                            },
                            "color": "secondary",
                        },
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "❓ Помощь",
                            },
                            "color": "secondary",
                        },
                    ],
                ],
            }

            self.vk.method(
                "messages.send",
                {
                    "user_id": user_id,
                    "message": "Выбери действие:",
                    "keyboard": json.dumps(keyboard),
                    "random_id": randrange(10**7),
                },
            )

            self.logger.info(f"Клавиатура отправлена пользователю user_id {user_id}")
        except vk_api.exceptions.ApiError as e:
            self.logger.error(
                f"Ошибка VK API при отправке клавиатуры пользователю user_id={user_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            self.logger.error(
                f"Неожиданная ошибка в send_start_keyboard: {e}", exc_info=True
            )
    def keyboard_dating(self, user_id):
        self.logger.info('Отправка клавиатуры знакомст пользователю')
        try:
            keyboard = {
                "one_time": False,
                "buttons": [
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "⏭️ Следующая анкета",
                            },
                            "color": "primary",
                        },
                        {
                            "action": {
                                "type": "text",
                                "label": "💘 Добавить в избранное",
                            },
                            "color": "secondary",
                        },
                    ],
                    [
                        {
                            "action": {
                                "type": "text",
                                "label": "◀️ Вернуться в главное меню",
                            },
                            "color": "secondary",
                        },
                    ],
                ],
            }

            self.vk.method(
                "messages.send",
                {
                    "user_id": user_id,
                    "message": "Выбери действие:",
                    "keyboard": json.dumps(keyboard),
                    "random_id": randrange(10**7),
                },
            )

            self.logger.info(f"Клавиатура отправлена пользователю user_id {user_id}")
        except vk_api.exceptions.ApiError as e:
            self.logger.error(
                f"Ошибка VK API при отправке клавиатуры пользователю user_id={user_id}: {e}",
                exc_info=True,
            )
        except Exception as e:
            self.logger.error(
                f"Неожиданная ошибка в send_start_keyboard: {e}", exc_info=True
            )

    def send_message(self, user_id, message):
        try:
            self.vk.method(
                "messages.send",
                {
                    "user_id": user_id,
                    "random_id": randrange(10**7),
                    "message": message,
                },
            )
            self.logger.info(f'Сообщение отправлено пользователю с ID:{user_id}')
        except vk_api.exceptions.VkApiError as e:
            self.logger.error(f'Ошибка VK API: {e}', exc_info=True)
        except Exception as e:
            self.logger.error(f'Непредвиденная ошбика при отправки:\n{e}', exc_info=True)

    def format_user_profile(self, user_id, your_profile=False):

        if not your_profile:
            user = self.search_user_by_parameters(user_id)
        else:
            user = self.get_user_data(user_id)

        if not user:
            if your_profile:
                return "😔 Не удалось получить данные твоего профиля."
            else:
                return "😔 Не удалось найти подходящих пользователей. Попробуй ещё раз!"



        sex_map = {1: 'Женский', 2: 'Мужской'}
        sex = sex_map.get(user.get('sex', 0), 'Не указан')  
        city_name = user.get('city', {}).get('title', 'Не указан')
        
        start_message = 'Анекта пользвателя: ' if not your_profile else 'Твоя анкета: '
        message = f"""
                    {start_message}
                        Имя : {user['first_name']}
                        Фамилия: {user['last_name']}
                        Пол: {sex},
                        Дата рождения: {user.get('bdate', 'не указана')}
                        Город: {city_name}
            """
        return message

    def search_user_by_parameters(self, user_id):
        current_user = self.get_user_data(user_id)

        if not current_user:
            self.logger.warning(f'Не удалось найти пользователя под id{user_id}')
            return []

        random_offset = randint(0, 999)

        user_sex = current_user.get('sex', 0)
        if user_sex == 0:
            self.logger.debug(f'Не удалось определить пол, поиск отменяется')
            return None

        sex = 1 if user_sex == 2 else 2
        users = self.vk_user.method(
            "users.search",
            {
                "count": 1,
                'offset' : random_offset,
                "has_photo": 1,
                "online": 1,
                "sex": sex,
                'fields' : 'sex, city, bdate',
                
            },
        )

        if user := users.get('items', []):
            return user[0]
        else:
            self.logger.warning('Не найдено пользователей по критериям поиска')
            return None

    def get_user_data(self, user_id):
        try:
            user_parameters = self.vk.method(
                "users.get",
                {
                    "user_ids": user_id,
                    "fields": "first_name, last_name, sex, bdate ,city",
                },
            )
            if not user_parameters:
                self.logger.debug(
                    f"Данные пользователя с id={user_id} извлечь не удалось"
                )
                return None

            self.logger.info(f"Данные для пользователя user_id={user_id} получены")
            return user_parameters[0]
        except vk_api.exceptions.VkApiError as e:
            self.logger.error(
                f"Ошибка VK API при извлечения данных пользователя={user_id}: {e}",
                exc_info=True,
            )
            return None

    def handle_message(self, event):
        """Обработка входящего сообщения"""
        user_id = event.user_id
        text = event.text.lower().strip()

        self.logger.info(f'Сообщение от user_id={user_id}: "{text}"')
        # Обработка команд
        try:
            if text in ["начать", "привет", "start"]:
                self.send_start_keyboard(user_id)

            elif text == "🔍 поиск":
                self.send_message(user_id, self.format_user_profile(user_id, False))
                self.keyboard_dating(user_id)
            
            elif text == "⏭️ следующая анкета":
                self.send_message(user_id, self.format_user_profile(user_id, False))

            elif text == "◀️ вернуться в главное меню":
                self.send_start_keyboard(user_id)

            elif text == "👤 профиль":
                self.send_message(user_id, self.format_user_profile(user_id, True))

            elif text == "❓ помощь":
                help_text = """
                Доступные команды:
                🔍 Поиск - поиск анкет
                👤 Профиль - твоя анкета
                ❓ Помощь - это сообщение
                """
                self.send_message(user_id, help_text.strip())
                self.send_start_keyboard(user_id)

            else:
                self.send_message(user_id, "Не понял команду. Нажми '❓ Помощь'")
        except Exception as e:
            self.logger.error(
                f"Непредвиденная ошибка при обработке команд user_id:{user_id}: {e}",
                exc_info=True,
            )

    def start(self):
        try:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event)
        except KeyboardInterrupt:
            print("Бот остановлен")
