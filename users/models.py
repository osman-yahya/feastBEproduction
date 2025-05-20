from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=20)
    email = models.CharField(max_length=100 , unique=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=40 , unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True , default='profile_pictures/default.jpeg')
    about = models.CharField(max_length=255, null=True, blank=True)
    followers = models.BigIntegerField(default=0)
    isRestaurant = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']