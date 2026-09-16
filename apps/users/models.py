from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [("farmer", "Agriculteur"), ("admin", "Administrateur")]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="farmer")
    telephone = models.CharField(max_length=30, blank=True)

    @property
    def is_agriculteur(self):
        return self.role == "farmer"
