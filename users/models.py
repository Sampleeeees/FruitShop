from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

User = get_user_model()

class Message(models.Model):
    """
    Models для збереження повідомлень які відправив користувач
    """
    user_id = models.ForeignKey(User, verbose_name='Відправник повідомлення', on_delete=models.CASCADE)
    message = models.CharField(max_length=750)
    date_send = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-id',)

