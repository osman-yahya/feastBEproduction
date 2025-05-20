from django.contrib import admin
from .models import Restaurant,Menu


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id','owner', 'name', 'is_active', 'menu', 'location', 'phone', 'about', 'profile_picture')  # Görünecek sütunlar
    search_fields = ('name', 'owner')  # Arama yapabilmek için
    list_filter = ('is_active',)  # Filtreleme seçenekleri


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('id','owner', 'name', 'content')  # Görünecek sütunlar
    search_fields = ('owner','name')  # Arama yapabilmek için
