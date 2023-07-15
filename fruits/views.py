import datetime

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from users.models import Message
from .models import Fruit, PersonalAccount, Declaration
from .tasks import buh_audit_task

User = get_user_model()

# Create your views here.


def index(request):
    return render(request, 'fruits/index.html', context={'messages': Message.objects.all().order_by('pk')[:40],
                                                         'fruits': Fruit.objects.all(),
                                                         'balance': PersonalAccount.objects.first(),
                                                         'declarations': Declaration.objects.filter(date__gte=datetime.datetime.today()).count})


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
    return redirect('index')


def start_audit(request):
    if request.method == 'GET':
        buh_audit_task(request.GET.get('user_id'))
        return JsonResponse({}, status=200)

def load_declaration(request):
    if request.method == 'POST':
        declaration = request.FILES.get('declaration')
        Declaration.objects.create(document=declaration, date=datetime.datetime.now(),
                                   personal_account=PersonalAccount.objects.first())
        declarations = Declaration.objects.filter(date__gte=datetime.datetime.today()).count()
        return JsonResponse({"success": declarations}, status = 200)



