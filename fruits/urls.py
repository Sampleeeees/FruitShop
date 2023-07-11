from django.urls import path, include
from .views import index, Login, user_logout

urlpatterns = [
    path('', index, name='index'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', user_logout, name='logout'),
]
