import asyncio
import datetime
import random
import time
from typing import Union

from asgiref.sync import async_to_sync, sync_to_async

from .models import TypeOperationChoices
from fruits.models import User
from channels.layers import get_channel_layer
from config.celery import app
#from django_celery_beat.models import PeriodicTask, PeriodicTasks, IntervalSchedule
from .models import Fruit, PersonalAccount


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

    asyncio.run((channel_layer.group_send(
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
                                   })))

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

    asyncio.run((channel_layer.group_send(
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
                      })))


@app.task()
def buh_audit_task():
    channel_layer = get_channel_layer()
    print('Channel', channel_layer)
    async_to_sync(channel_layer.group_send)(
        'audit_audit',  # Назва групи WebSocket
        {'type': 'bgh_audit_message',
         'progress': 0}
    )
    for i in range(1, 16):
        progress = i * 100 / 15  # Обраховуємо відсоток прогресу
        print(progress)
        # Відправляємо прогрес задачі до фронтенду через WebSocket
        async_to_sync(channel_layer.group_send)(
            'audit_audit',  # Назва групи WebSocket
            {'type': 'bgh_audit_message',
             'progress': progress}
        )
        time.sleep(1)

        # Відправка прогресу через WebSocket


