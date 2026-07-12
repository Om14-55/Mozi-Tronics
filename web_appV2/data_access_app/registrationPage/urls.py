from django.urls import path
from registrationPage.views import RegistrationPage


urlpatterns = [
    path('', RegistrationPage.as_view(), name='registrationPage'),
]