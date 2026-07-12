from django.urls import path
from loginPage.views import LoginPage

urlpatterns = [
    path('', LoginPage.as_view(), name="loginPage"),
]