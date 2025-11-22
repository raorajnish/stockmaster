from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    is_manager = models.BooleanField('Is Manager', default=False)
    is_w_staff = models.BooleanField('Is Warehouse Staff', default=False)
