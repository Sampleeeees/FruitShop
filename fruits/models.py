from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
User = get_user_model()

#class Transaction(models.Model):
#    count = models.PositiveIntegerField(default=0, verbose_name='Кількість певного продукту')
#    date_buy = models.DateTimeField(auto_now=True, verbose_name='Дата купівлі продукту')
#    price = models.PositiveIntegerField(default=0, verbose_name='Ціна за одиницю продукту')

class TypeOperationChoices(models.TextChoices):
    """
    Choices для вибору типу операції над продуктом
    """
    buy = ('Купити', 'Купити')
    sell = ('Продати', 'Продати')

class Fruit(models.Model):
    """
    Models продукту в якій вказується назва, ціна, кількість купленого/проданого, тип операції, та дата операції над продуктом
    """
    name = models.CharField(max_length=75, verbose_name='Назва продукту')
    total_count = models.PositiveIntegerField(default=0, verbose_name='Загальна кількість продукту')
    price = models.PositiveIntegerField(default=0, verbose_name='Ціна за одиницю продукту')
    count = models.PositiveIntegerField(default=0, verbose_name='Кількість купленого чи проданого продукту')
    type_operation = models.CharField(choices=TypeOperationChoices.choices, verbose_name='Дію з продуктом', max_length=10)
    date_operation = models.DateTimeField(auto_now=True, verbose_name='Дата дії над продуктом')

    @property
    def summ(self):
        return self.price * self.count

class PersonalAccount(models.Model):
    """
    Models для банківського рахунку користувача в якому зберігається його баланс
    """
    user = models.ForeignKey(User, verbose_name='Користувач', on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0, verbose_name='Баланс користувача')

class Declaration(models.Model):
    """
    Models для збереження декларації по особовому рахунку
    """
    document = models.FileField(upload_to='declaration/', verbose_name='Файл декларації')
    date = models.DateTimeField(auto_now=True, verbose_name='Дата та час завантаження декларації')
    personal_account = models.ForeignKey(PersonalAccount, verbose_name='Банківський рахунок', on_delete=models.CASCADE)


