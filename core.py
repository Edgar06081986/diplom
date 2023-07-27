from pprint import pprint
import vk_api
from vk_api.exceptions import ApiError
from config import acces_token
from datetime import datetime

class VkTools:
    def __init__(self, acces_token):
        self.vkapi = vk_api.VkApi(token=acces_token)

    def get_profile_info(self, user_id):
        try:
            info = self.vkapi.method('users.get', {'user_id': user_id, 'fields': 'city,sex,relation,bdate'})
            pprint(info)  # Отладочный вывод
        except ApiError as e:
            info = {}
            print(f'error = {e}')

        if isinstance(info, list) and len(info) > 0:
            info = info[0]

        result = {
            'name': info.get('first_name', '') + ' ' + info.get('last_name', ''),
            'sex': info.get('sex'),
            'city': info.get('city', {}).get('title') if info.get('city') is not None else None,
            'year': datetime.now().year - int(info.get('bdate').split('.')[2]) if info.get('bdate') is not None else None
        }
        return result

    def search_worksheet(self, params, offset):
        try:
            users = self.vkapi.method('users.search', {
                'count': 10,
                'offset': offset,
                'hometown': params['city'],
                'sex': 1 if params['sex'] == 2 else 2,
                'has_photo': True,
                'age_from': params['year'] - 3,
                'age_to': params['year'] + 3,
            })
        except ApiError as e:
            users = []
            print('Внимание ошибка!!')
            print(f'error = {e}')

        result = [
            {'name': item['first_name'] + ' ' + item['last_name'], 'id': item['id']}
            for item in users['items']
            if not item.get('is_closed', True)
        ]

        return result

    def get_photos(self, id):
        try:
            photos = self.vkapi.method('photos.get', {
                'owner_id': id,
                'album_id': 'profile',
                'extended': 1
            })
        except ApiError as e:
            photos = {}
            print(f'error = {e}')

        result = [
            {
                'owner_id': item['owner_id'],
                'id': item['id'],
                'likes': item['likes']['count'],
                'comments': item['comments']['count']
            }
            for item in photos['items']
        ]

        result.sort(key=lambda x: (x['likes'], x['comments']), reverse=True)
        return result[:3]


if __name__ == '__main__':
    user_id = 613515737
    tools = VkTools(acces_token)
    params = tools.get_profile_info(user_id)
    worksheets = tools.search_worksheet(params, 20)
    worksheet = worksheets.pop()
    photos = tools.get_photos(worksheet['id'])
    pprint(worksheets)
