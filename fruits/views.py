from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from users.models import Message
from .models import Fruit, PersonalAccount
from .tasks import buh_audit_task

User = get_user_model()

# Create your views here.


def index(request):
    return render(request, 'fruits/index.html', context={'messages': Message.objects.all().order_by('pk')[:40],
                                                         'fruits': Fruit.objects.all(),
                                                         'balance': PersonalAccount.objects.first()})


class Login(LoginView):
    success_url = reverse_lazy('index')

    def post(self, request, *args, **kwargs):
        user = request.POST.get('username')
        password = request.POST.get('password')
        if user and password:
            try:
                fruit_user = User.objects.get(username=user)
                if fruit_user and fruit_user.check_password(password):
                    login(request, user=fruit_user)
                    return redirect(self.success_url)
            except User.DoesNotExist:
                return render(request, 'fruits/index.html', context={'msg_error': _('Ви ввели невірний логін чи пароль.'
                                                                                 'Перевірте дані та спробуйте ще раз'),
                                                                     })
        return render(request, 'fruits/index.html', context={'msg_error': _('Введіть логін та пароль')})


def user_logout(request):
    logout(request)
    return render(request, 'fruits/index.html')


def start_audit(request):
    if request.method == 'GET':
        buh_audit_task()
        return JsonResponse({}, status=200)



