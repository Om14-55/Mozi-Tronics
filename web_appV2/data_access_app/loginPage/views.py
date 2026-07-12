from django.shortcuts import render, redirect
from django.views import View

# Create your views here.
class LoginPage(View):
    def get(self, request):
        if 'user_id' in request.session:
            return redirect('dashboard')
        
        return render(request, "loginPage.html")
