from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('search_result/', views.search_result, name='search_result'),
    path('search_detail/<str:id>/', views.search_detail, name='search_detail'),
    path('delete_review_file/<int:id>/', views.delete_review_file, name='delete_review_file'),
]
