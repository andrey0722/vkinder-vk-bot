import os
import dotenv
import vk_api
dotenv.load_dotenv()
token = os.environ['TOKEN']
vk = vk_api.VkApi(token=token)

def show_personal_info(personal_vk_id):

    person_data = vk.method("users.get", {"user_ids": personal_vk_id , "fields": "nickname, first_name, last_name, city, sex, bdate, domain, photo_50, online"})

    # print(f'Никнейм: {person_data[0]['nickname']}')
    vk_firstname = person_data[0]['first_name']
    vk_lastname = person_data[0]['last_name']
    vk_yearofbirth = person_data[0].get('bdate', 'не указан').split('.')[-1]
    vk_city = person_data[0].get('city', '')['title'] if person_data[0].get('city', '') else 'не указан'
    vk_sex = 'Женский' if person_data[0]['sex'] == 1 else 'Мужской' if person_data[0]['sex'] == 2 else 'Не указан'
    vk_url = f'https://vk.com/{person_data[0]['domain']}'
    vk_online = 'Да' if person_data[0]['online'] == 1 else 'Нет'

    print(f'Имя: {vk_firstname}')
    print(f'Фамилия: {vk_lastname}')
    print(f'Год рождения: {vk_yearofbirth}')
    print(f'Город проживания: {vk_city}')
    print(f'Пол: {vk_sex}')
    print(f'Ссылка на страницу профиля: {vk_url}')
    print(f'Сейчас в сети: {vk_online}')

    return [vk_firstname, vk_lastname, vk_yearofbirth, vk_city, vk_sex, vk_url, vk_online]

if __name__ == '__main__':
    show_personal_info(1076055746)
    print('-' * 25)
    show_personal_info(771666895)
    print('-' * 25)



