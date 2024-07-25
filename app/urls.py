from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('search_result/', views.search_result, name='search_result'),
    path('search_detail/<int:restaurant_id>/', views.search_detail, name='search_detail'),
]
