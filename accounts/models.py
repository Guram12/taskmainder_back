from django.db import models
from django.contrib.auth.models import AbstractUser





class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True , blank=True , null=True)
    phone_number = models.CharField(max_length=25, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email




































