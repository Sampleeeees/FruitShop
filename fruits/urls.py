from django.urls import path, include
from .views import index, Login, user_logout, start_audit

urlpatterns = [
    path('', index, name='index'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', user_logout, name='logout'),
    path('start_audit', start_audit, name='start_audit')
]
