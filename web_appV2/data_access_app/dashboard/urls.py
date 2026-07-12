from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from dashboard.views import Dashboard

urlpatterns = [
    path('', Dashboard.as_view(), name='dashboard'),
]