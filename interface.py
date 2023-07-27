import re
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from datetime import datetime
from config import comunity_token, acces_token
from core import VkTools
from data_store import check_user, addUser, engine

class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.keys = []
        self.offset = 0

    def messageSend(self, userID, **kwargs):
        data = {}
        data["attachment"] = None
        data = kwargs
        data["random_id"] = get_random_id()
        data["user_id"] = userID
        self.vk.method('messages.send', data)
    @staticmethod
    def _birthDate_toYear(bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)
    def photos_for_send(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
        return photo_string

    def new_message(self, k):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                event_text = event.text

                if k == 0:
                    if any(char.isdigit() for char in event_text):
                        self.messageSend(event.user_id, message = 'Пожалуйста, введите имя и фамилию без чисел')
                    else:
                        return event_text
                if k == 1:
                    if event_text == "М" or event_text == "Ж":
                        return int(event_text)
                    else:
                        self.messageSend(event.user_id,  message = 'Неверный формат ввода пола. Введите М или Ж')
                if k == 2:
                    if any(char.isdigit() for char in event_text):
                        self.messageSend(event.user_id,  message = 'Неверно указан город. Введите название города без чисел')
                    else:
                        return event_text

                if k == 3:
                    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
                    if not re.match(pattern, event_text):
                        self.messageSend(event.user_id,  message = 'Пожалуйста, введите вашу дату рождения в формате (ДД.ММ.ГГГГ)')
                    else:
                        return self._birthDate_toYear(event_text)

    def sendMesExec(self, event):
        if self.params['name'] is None:
            self.messageSend(event.user_id,  message = 'Введите ваше имя и фамилию')
            return self.new_message(0)

        if self.params['sex'] is None:
            self.messageSend(event.user_id,  message = 'Введите свой пол (М или Ж)')
            return self.new_message(1)

        elif self.params['city'] is None:
            self.messageSend(event.user_id,  message = 'Введите город')
            return self.new_message(2)

        elif self.params['year'] is None:
            self.messageSend(event.user_id,  message = 'Введите дату рождения (ДД.ММ.ГГГГ)')
            return self.new_message(3)

    def change_city(self, event):
        self.messageSend(event.user_id,  message = 'Введите новый город')
        city = self.new_message(2)
        self.params['city'] = city
        self.messageSend(event.user_id, message =f'Город изменен на: {city}')

    def process_worksheet(self, engine, user_id, worksheet):
        if check_user(engine, user_id, worksheet['id']):
            addUser(engine, user_id, worksheet['id'])
            return worksheet
        return None

    def get_profile(self, worksheets, event):
        while True:
            if worksheets:
                worksheet = worksheets.pop()
                result = self.process_worksheet(engine, event.user_id, worksheet)
                if result is not None:
                    yield result
            else:
                worksheets = self.vk_tools.search_worksheet(self.params, self.offset)

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                text = event.text.lower()
                if text == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.messageSend(event.user_id,  message = f'Привет, {self.params["name"]}!')
                    self.keys = self.params.keys()
                    for i in self.keys:
                        if self.params[i] is None:
                            self.params[i] = self.sendMesExec(event)
                    self.messageSend(event.user_id, message = 'Регистрация пройдена! Искать пару командой "Поиск"')
                elif text == 'поиск':
                    self.messageSend(event.user_id, message = 'Начинаем поиск...')
                    msg = next(iter(self.get_profile(self.worksheets, event)))
                    if msg:
                        photoString = self.photos_for_send(msg)
                        self.offset += 10
                        self.messageSend(event.user_id, message = f'Имя: {msg["name"]} Ссылка: vk.com/id{msg["id"]}', attachment=photoString)
                elif text == 'пока':
                    self.messageSend(event.user_id, message = 'Увидимся!')
                elif text == 'поменять город':
                    self.change_city(event)
                elif text == 'помощь':
                    commands = [
                        'Привет - запуск бота',
                        'Поменять город - изменить город',
                        'Поиск - найти пару'
                        'Пока - завершение работы с ботом'
                    ]
                    self.messageSend(event.user_id, message = 'Доступные команды:\n' + '\n'.join(commands))
                else:
                    self.messageSend(event.user_id, message = 'Неизвестная команда')

if __name__ == '__main__':
    botInterface = BotInterface(comunity_token, acces_token)
    botInterface.event_handler()