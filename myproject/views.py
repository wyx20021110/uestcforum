from django.shortcuts import render

def home(request):
    """网站主页"""
    return render(request, 'index.html') 