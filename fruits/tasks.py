import datetime
import random
from .models import TypeOperationChoices

from config.celery import app
#from django_celery_beat.models import PeriodicTask, PeriodicTasks, IntervalSchedule
from .models import Fruit



#@app.task
def fruit_buy_task(fruit_id, count=None):
    fruit = Fruit.objects.get(pk=fruit_id)
    if count:
        fruit.count = count
    else:
        fruit.count = random.randint(1, 5)
    fruit.price = 4 if fruit.name == 'Яблука' else 1 if fruit.name == 'Банани' else 3 if fruit.name == 'Ананаси' else 2
    summa = fruit.price * fruit.count
    # Додати баланс який буде відніматися після покупки товару
    fruit.total_count -= int(count)
    print(TypeOperationChoices.choices[0])
    fruit.type_operation = TypeOperationChoices.choices[0][0]
    fruit.date_operation = datetime.datetime.now()
    fruit.save()
    print('New Fruit ', fruit)

def fruit_sell_task(fruit_id, count=None):
    fruit = Fruit.objects.get(pk=fruit_id)
    if count:
        fruit.count = count
    else:
        fruit.count = random.randint(1, 5)
    fruit.price = 5 if fruit.name == 'Яблука' else 2 if fruit.name == 'Банани' else 4 if fruit.name == 'Ананаси' else 3
    summa = fruit.price * fruit.count
    fruit.total_count += int(count)
    fruit.type_operation = TypeOperationChoices.choices[1][0]
    fruit.date_operation = datetime.datetime.now()
    fruit.save()



if __name__ == "__main__":
    result = fruit_buy_task(1, 5)
    print(result)