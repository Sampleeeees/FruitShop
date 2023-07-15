from django.core.management import BaseCommand
from fruits.models import *
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(username='Joker').exists():
            User.objects.create(username='Joker', email='joker@email.com')

        if not User.objects.filter(username="anonymous").exists():
            User.objects.create(username='anonymous', email='anonymousm@email.com')

        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create(username='admin', email='admin@email.com', is_staff=True, is_superuser=True)
            admin.set_password("admin")
            admin.save()
            PersonalAccount.objects.create(balance=1000)