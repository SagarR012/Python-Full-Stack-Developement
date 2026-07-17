from django.shortcuts import render, redirect

from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import LoginForm

def login_view(request):
    form = LoginForm(request, data = request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            messages.success(request, f'welcome back,{user.username}!')
            return redirect('book_list')
        else:
            messages.error(request, 'invalid username or password.')
    return render(request, 'accony/login.html',{'form':form})
# create your views here
def logout_view(request):
    logout(request)
    return redirect('login')
