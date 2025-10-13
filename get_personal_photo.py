import os
from pprint import pprint
import dotenv
import vk_api

def get_personal_photo(personal_vk_id):
    ''' Функция возвращает список трех самых популярных по количеству лайков фотографий '''
    dotenv.load_dotenv()
    token = os.environ['TOKEN3']
    vk = vk_api.VkApi(token=token)

    try:
        result = vk.method(
            'photos.get',
            {
                'owner_id': personal_vk_id,
                'album_id': 'profile',
                'extended': 1,
                'photo_ids': 0,
            },
        )

        lst_out = []
        best_photos = []
        number_of_photos = result['count']

        for i in range(number_of_photos):
            number_of_likes = result['items'][i]['likes']['count']
            photo_id = result['items'][i]['id']
            # owner_id = result['items'][i]['owner_id']
            orig_photo_url = result['items'][i]['orig_photo']['url']
            lst_out.append((photo_id, number_of_likes, orig_photo_url))

        best_photos = [j for j in sorted(lst_out, key=lambda lst: lst[1], reverse=True)][:3]
        print(f'Всего фотографий: {number_of_photos}', 'Самые популярные по количеству лайков:', sep = '\n')

        return best_photos

    except (vk_api.exceptions.ApiError, UnboundLocalError):
        return 'Профиль является приватным'

if __name__ == '__main__':
    pprint(get_personal_photo(244591279))
    print('-' * 50)
    pprint(get_personal_photo(244591270))
    print('-' * 50)
    pprint(get_personal_photo(822356301))