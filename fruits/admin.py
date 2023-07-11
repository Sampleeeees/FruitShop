from django.contrib import admin
from .models import *
# Register your models here.


@admin.register(Fruit)
class FruitAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_count', 'price', 'count', 'type_operation', 'date_operation')