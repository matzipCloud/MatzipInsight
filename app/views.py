from django.shortcuts import render, redirect
import requests

# Create your views here.

def home(request):
    return render(request, 'app/home.html')

def search_result(request):
    return render(request, 'app/search_result.html')

def search_detail(request):
    return render(request, 'app/search_detail.html')