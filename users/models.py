from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    avatar = models.URLField(blank=True)
    bio = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return self.username


