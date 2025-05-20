from django.contrib import admin
from .models import User

# User modelini admin paneline kaydediyoruz
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'username')  # Görünecek sütunlar
    search_fields = ('email', 'username')  # Arama yapabilmek için
    list_filter = ('is_staff', 'is_active')  # Filtreleme seçenekleri
