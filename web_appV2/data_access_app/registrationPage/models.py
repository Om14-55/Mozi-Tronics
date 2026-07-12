# from django.contrib.auth.models import AbstractUser
# from django.db import models

# # Create your models here.
# class UserProfile(models.Model):
#     username = models.CharField(max_length=50, unique=True)
#     email = models.EmailField(unique=True)
#     gender = models.CharField(max_length=15)
#     password = models.CharField(max_length=255)
#     phone_number = models.CharField(max_length=10)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.username