import datetime
import json
from channels.db import database_sync_to_async
from users.models import User, Message
from .models import Fruit
from .tasks import fruit_buy_task, fruit_sell_task
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.db.models import Manager

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'chat'
        self.room_group_name = "chat_%s" % self.room_name

        # Вхід в групу кімнати
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        # Вихід з групи кімнати
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Отримання повідомлення з Websocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Відправити повідомлення в групу
        if message:
            new_msg = await self.save_message_to_db(message, self.scope['user'])
            time_send = new_msg.date_send + datetime.timedelta(hours=3)
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message",
                                       "message": new_msg.message,
                                       "time": time_send.strftime("%H:%M"),
                                       "user": new_msg.user_id.username}
            )

    # Збереження повідомлення в базу даних
    @database_sync_to_async
    def save_message_to_db(self, message: str, user) -> Message:
        if not user.is_authenticated:
            user = User.objects.get(username='anonymous')
        new_message = Message.objects.create(
            user_id=user,
            message=message
        )
        return new_message

    # Отримання повідомлення для групи кімнати
    async def chat_message(self, event):
        message = event['message']
        time = event['time']
        user = event['user']

        # Відправити повідомлення на Websocket
        await self.send(text_data=json.dumps({'message': message,
                                              'time': time,
                                              'user': user}))

class FruitConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'shop'
        self.room_group_name = 'shop_%s' % self.room_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if self.scope['user'].is_anonymous:
            await self.send(text_data=json.dumps({
                "error": "Авторизуйтесь в системі"
            }))
        text_data_json = json.loads(text_data)
        fruit_id = text_data_json['fruit_id']
        count = text_data_json['count']
        if fruit_id and count:
            if text_data_json['action'] == 'buy':
                print('Buy fruit')
                await sync_to_async(fruit_buy_task)(fruit_id, count)
                fruit = await sync_to_async(Fruit.objects.get)(pk=fruit_id)
                balance = await sync_to_async(lambda: fruit.total_count)()
                date_operation = fruit.date_operation + datetime.timedelta(hours=3)
                print(balance)
                await self.channel_layer.group_send(
                    self.room_group_name, {'type': 'fruit_message',
                                           'fruit_id': fruit_id,
                                           'total_count': balance,
                                           'last_operation': f'{date_operation.strftime("%d.%m.%Y %H:%M")} - куплено {fruit.count}'
                                                              f' {fruit.name.lower()} за {fruit.summ} USD'
                })
            elif text_data_json['action'] == 'sell':
                print('Sell fruit')
                await sync_to_async(fruit_sell_task)(fruit_id, count)
                fruit = await sync_to_async(Fruit.objects.get)(pk=fruit_id)
                balance = await sync_to_async(lambda: fruit.total_count)()
                date_operation = fruit.date_operation + datetime.timedelta(hours=3)
                await self.channel_layer.group_send(
                    self.room_group_name, {'type': 'fruit_message',
                                           'fruit_id': fruit_id,
                                           'total_count': balance,
                                           'last_operation': f'{date_operation.strftime("%d.%m.%Y %H:%M")} - продано {fruit.count}'
                                                             f' {fruit.name.lower()} за {fruit.summ} USD'
                                           })
                pass #taska for sell fruit
        else:
            await self.send(text_data=json.dumps({
                "error": "Кількість повинна бути введена цифрою",
            }))

    async def fruit_message(self, event):
        fruit_id = event['fruit_id']
        total_count = event['total_count']
        last_operation = event['last_operation']

        await self.send(text_data=json.dumps({
            'fruit_id': fruit_id,
            'total_count': total_count,
            'last_operation': last_operation
        }))
