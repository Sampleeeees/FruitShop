import datetime
import json
from typing import Callable, Union

from channels.db import database_sync_to_async
from users.models import User, Message
from .models import Fruit, PersonalAccount, TypeOperationChoices
from .tasks import buh_audit_task
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from django.db.models import Manager

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket для чату в FruitShop
    """
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
    """
    WebSocket для операцій над фруктами та банківським рахунком
    """
    async def connect(self):
        self.room_name = 'shop'
        self.room_group_name = 'shop_%s' % self.room_name

        print('Fruit Consumer Chat Group', self.room_group_name)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def fruit_balance(self, fruit_id: int, count: int, text: str) -> None:
        print('ID', fruit_id, 'Count', count, 'text', text)
        """
        Функція для передачі даних про фрукт, баланс, оновленну кількість фрукту, та дату операції яка повертає у
        ВебСокет повідомлення про результат операції
        """
        fruit = await sync_to_async(Fruit.objects.get)(pk=fruit_id)
        user_balance = await sync_to_async(PersonalAccount.objects.first)()
        date_operation = fruit.date_operation + datetime.timedelta(hours=3)
        trans = ''
        summa = 0
        if text == 'куплено':
            fruit.price = 4 if fruit.name == 'Яблука' else 1 if fruit.name == 'Банани' else 3 if fruit.name == 'Ананаси' else 2
            summa = int(fruit.price) * int(count)
            if user_balance.balance >= int(summa):
                user_balance.balance -= int(summa)
                fruit.total_count += int(count)
                fruit.type_operation = TypeOperationChoices.choices[0][0]
                fruit.count = count
                await sync_to_async(fruit.save)()
                trans = True
            else:
                trans = 'error balance'
        elif text == 'продано':
            fruit.price = 5 if fruit.name == 'Яблука' else 2 if fruit.name == 'Банани' else 4 if fruit.name == 'Ананаси' else 3
            summa = int(fruit.price) * int(count)
            if int(fruit.total_count) >= int(count):
                user_balance.balance += int(summa)
                fruit.total_count -= int(count)
                fruit.type_operation = TypeOperationChoices.choices[1][0]
                fruit.count = count
                await sync_to_async(fruit.save)()
                trans = 'sell fruit'
            else:
                trans = 'error fruit'
        await sync_to_async(user_balance.save)()
        balance = await sync_to_async(lambda: fruit.total_count)()

        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'fruit_message',
                                   'fruit_id': fruit_id,
                                   'total_count': balance,
                                   'last_operation': f'{date_operation.strftime("%d.%m.%Y %H:%M")} - {text} {fruit.count}'
                                                     f' {fruit.name.lower()} за {fruit.summ} USD',
                                   'transaction': trans,
                                   'date_transaction': date_operation.strftime("%d.%m.%Y %H:%M"),
                                   'fruit_count': count,
                                   'fruit_name': fruit.name.lower(),
                                   'fruit_price': fruit.price,
                                   'account_balance': user_balance.balance
                                   })

    async def update_balance(self, personal_balance: int, is_positive: bool) -> None:
        """
        Функція для оновлення балансу рахунку та відправки нових даних у Веб сокет
        """
        user_balance = await sync_to_async(PersonalAccount.objects.first)()
        if is_positive:
            user_balance.balance += int(personal_balance)
        else:
            user_balance.balance -= int(personal_balance)
        time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        await sync_to_async(user_balance.save)()

        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'balance_message',
                                   'new_balance': user_balance.balance,
                                   'time': time,
                                   'success': is_positive,
                                   'added_balance': personal_balance}
        )

    async def receive(self, text_data=None, bytes_data=None):
        if self.scope['user'].is_anonymous:
            return await self.send(text_data=json.dumps({
                "error": "Авторизуйтесь в системі"
            }))
        text_data_json = json.loads(text_data)
        if text_data_json['action'] == 'add balance':
            new_balance = text_data_json['account_balance']
            await self.update_balance(personal_balance=new_balance, is_positive=True) # Відправка даних на Вебсокет про поповнення балансу
        elif text_data_json['action'] == 'sell balance':
            new_balance = text_data_json['account_balance']
            await self.update_balance(personal_balance=new_balance, is_positive=False) # Відправка даних на Вебсокет про зняття балансу
        elif text_data_json['action'] == 'buy' or text_data_json['action'] == 'sell':
            fruit_id = text_data_json['fruit_id']
            count = text_data_json['count']
            if fruit_id and count:
                if text_data_json['action'] == 'buy':
                    print('Buy fruit')
                    await self.fruit_balance(fruit_id=fruit_id, count=count, text='куплено') # Відправка даних на вебсокет про купівлю фруктів
                elif text_data_json['action'] == 'sell':
                    print('Sell fruit')
                    await self.fruit_balance(fruit_id=fruit_id, count=count, text='продано') # Відправка даних на вебсокет про продаж фруктів

    async def fruit_message(self, event):
        message = event['type']
        fruit_id = event['fruit_id']
        total_count = event['total_count']
        last_operation = event['last_operation']
        transaction = event['transaction']
        date_transaction = event['date_transaction']
        fruit_name = event['fruit_name']
        fruit_count = event['fruit_count']
        fruit_price = event['fruit_price']
        account_balance = event['account_balance']

        await self.send(text_data=json.dumps({
            'type': message,
            'fruit_id': fruit_id,
            'total_count': total_count,
            'last_operation': last_operation,
            'transaction': transaction,
            'date_transaction': date_transaction,
            'fruit_name': fruit_name,
            'fruit_count': fruit_count,
            'fruit_price': fruit_price,
            'account_balance': account_balance,
        }))

    async def balance_message(self, event):
        message = event['type']
        added_balance = event['added_balance']
        time = event['time']
        success = event['success']
        new_balance = event['new_balance']

        await self.send(text_data=json.dumps({
            'type': message,
            'added_balance': added_balance,
            'time': time,
            'success': success,
            'balance': new_balance
        }))


class BuhAuditConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'audit'
        self.room_group_name = 'audit_%s' % self.room_name

        print('Buh', self.room_group_name)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def bgh_audit_message(self, event):
        print('Event', event)
        progress = event['progress']
        await self.send(text_data=json.dumps({
            'progress': progress
        }))

