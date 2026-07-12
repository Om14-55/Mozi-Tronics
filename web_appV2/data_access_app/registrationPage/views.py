from datetime import datetime
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import connection


# Create your views here.
class RegistrationPage(View):
    def get(self, request):
        if 'user_id' in request.session:
            return redirect('dashboard')
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT client_code, name FROM client_master_v2 ORDER BY client_code")
            clients = cursor.fetchall()

            cursor.execute("SELECT fact_code, factory_name FROM factory_master_v2 ORDER BY fact_code")
            factories = cursor.fetchall()

            cursor.execute("SELECT user_role, role_details FROM role_master_v2 ORDER BY id ASC")
            roles = cursor.fetchall()

        context = {
            'clients': clients,
            'factories': factories,
            'roles': roles,
        }

        return render(request, "registrationPage.html", context)