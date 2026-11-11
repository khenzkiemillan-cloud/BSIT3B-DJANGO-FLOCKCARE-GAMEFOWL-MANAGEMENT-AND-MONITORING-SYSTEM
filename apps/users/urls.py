from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User Profile / Settings
    path('profile/', views.user_profile_page, name='profile'),

    # Admin User Management
    path('', views.user_list_page, name='user_list'),
    path('ajax/list/', views.user_list_ajax, name='user_list_ajax'),
    path('ajax/get/<int:pk>/', views.user_get_ajax, name='user_get_ajax'),
    path('ajax/save/', views.user_save_ajax, name='user_save_ajax'),
    path('ajax/delete/<int:pk>/', views.user_delete_ajax, name='user_delete_ajax'),
]
