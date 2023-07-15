import asyncio
import datetime
import json
import random
import time
from typing import Union
import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.core.exceptions import MultipleObjectsReturned
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import IntervalSchedule, PeriodicTask, PeriodicTasks

from users.models import Message
from .models import TypeOperationChoices
from fruits.models import User
from channels.layers import get_channel_layer
from config.celery import app
from .models import Fruit, PersonalAccount


@app.on_after_finalize.connect()
def setup_periodic_task(sender, **kwargs):
    sender.add_periodic_task(5, joker.s(), name='joke')
    sender.add_periodic_task(6, fruit_buy.s(1), name='fruit_buy_apple')
    sender.add_periodic_task(9, fruit_buy.s(2), name='fruit_buy_banana')
    sender.add_periodic_task(12, fruit_buy.s(3), name='fruit_buy_pineapple')
    sender.add_periodic_task(15, fruit_buy.s(4), name='fruit_buy_peach')
    sender.add_periodic_task(15, fruit_sell.s(1), name='fruit_sell_apple')
    sender.add_periodic_task(12, fruit_sell.s(2), name='fruit_sell_banana')
    sender.add_periodic_task(9, fruit_sell.s(3), name='fruit_sell_pineapple')
    sender.add_periodic_task(6, fruit_sell.s(4), name='fruit_sell_peach')
    sender.add_periodic_task(40, balance_task.s(), name='balance_task')


@app.task()
def joker():
    channel_layer = get_channel_layer()
    joker = User.objects.get(username='Joker')
    response = httpx.get('https://v2.jokeapi.dev/joke/Any?type=single')
    joke = response.json()['joke']
    message = Message.objects.create(user_id=joker, message=joke)
    time_send = datetime.datetime.now()
    async_to_sync(channel_layer.group_send)(
        'chat_chat', {"type": "chat_message",
                      "message": message.message,
                      "time": time_send.strftime("%H:%M"),
                      "user": joker.username}
    )
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=len(joke),
        period=IntervalSchedule.SECONDS,
    )
    task = PeriodicTask.objects.get(task='fruits.tasks.joker')
    task.interval = schedule
    task.save()
    PeriodicTasks.changed(task)



@app.task()
def fruit_buy(fruit_id: int) -> None:
    print('Task buy fruit started')
    channel_layer = get_channel_layer()
    fruit = Fruit.objects.get(pk=fruit_id)
    fruit.price = 4 if fruit.name == 'Яблука' else 1 if fruit.name == 'Банани' else 3 if fruit.name == 'Ананаси' else 2
    balance = PersonalAccount.objects.first()
    count = random.randint(4, 8)
    summa = int(count) * int(fruit.price)
    if balance.balance >= summa:
        fruit.date_operation = datetime.datetime.now()
        fruit.count = count
        fruit.total_count += count
        balance.balance -= summa
        trans = True
        fruit.save()
        balance.save()
    else:
        trans = 'error balance'

    async_to_sync(channel_layer.group_send)(
            'shop_shop', {'type': 'fruit_message',
                                   'fruit_id': fruit_id,
                                   'total_count': fruit.total_count,
                                   'last_operation': f'{datetime.datetime.now().strftime("%d.%m.%Y, %H:%M")} - куплено {count}'
                                                     f' {fruit.name.lower()} за {fruit.summ} USD',
                                   'transaction': trans,
                                   'date_transaction': datetime.datetime.now().strftime("%d.%m.%Y, %H:%M"),
                                   'fruit_count': count,
                                   'fruit_name': fruit.name.lower(),
                                   'fruit_price': fruit.price,
                                   'account_balance': balance.balance
                                   })


@app.task()
def fruit_sell(fruit_id: int) -> None:
    channel_layer = get_channel_layer()
    fruit = Fruit.objects.get(pk=fruit_id)
    balance = PersonalAccount.objects.first()
    count = random.randint(5, 10)
    fruit.price = 5 if fruit.name == 'Яблука' else 2 if fruit.name == 'Банани' else 4 if fruit.name == 'Ананаси' else 3
    if int(fruit.total_count) >= int(count):
        summa = int(fruit.price) * int(count)
        balance.balance += summa
        fruit.count = count
        fruit.total_count -= count
        fruit.date_operation = datetime.datetime.now()
        fruit.save()
        balance.save()
        trans = 'sell fruit'
    else:
        trans = 'error fruit'

    async_to_sync(channel_layer.group_send)(
        'shop_shop', {'type': 'fruit_message',
                      'fruit_id': fruit_id,
                      'total_count': fruit.total_count,
                      'last_operation': f'{datetime.datetime.now().strftime("%d.%m.%Y, %H:%M")} - продано {count}'
                                        f' {fruit.name.lower()} за {fruit.summ} USD',
                      'transaction': trans,
                      'date_transaction': datetime.datetime.now().strftime("%d.%m.%Y, %H:%M"),
                      'fruit_count': count,
                      'fruit_name': fruit.name.lower(),
                      'fruit_price': fruit.price,
                      'account_balance': balance.balance
                      })


@app.task()
def balance_task():
    channel_layer = get_channel_layer()
    total_balance = PersonalAccount.objects.first()
    change = random.randint(150, 450)
    operation = random.choice(['add', 'subtract'])
    if operation == 'add':
        total_balance.balance += change
    elif operation == 'subtract':
        total_balance.balance -= change
    total_balance.save()
    async_to_sync(channel_layer.group_send)(
        'shop_shop', {"type": "balance_message",
                      "added_balance": change,
                      "time": datetime.datetime.now() + datetime.timedelta(hours=3),
                      "success": True if operation == 'add' else False,
                      "balance": total_balance.balance}
    )



@app.task()
def buh_audit_task(user_id):
    channel_layer = get_channel_layer()
    print('Channel', channel_layer)
    async_to_sync(channel_layer.group_send)(
        'audit_audit_',  # Назва групи WebSocket
        {'type': 'bgh_audit_message',
         'progress': 0}
    )
    for i in range(1, 16):
        progress = i * 100 / 15  # Обраховуємо відсоток прогресу
        print(progress)
        # Відправляємо прогрес задачі до фронтенду через WebSocket
        async_to_sync(channel_layer.group_send)(
            f'audit_audit_{user_id}',  # Назва групи WebSocket
            {'type': 'bgh_audit_message',
             'progress': progress}
        )
        time.sleep(1)

        # Відправка прогресу через WebSocket


