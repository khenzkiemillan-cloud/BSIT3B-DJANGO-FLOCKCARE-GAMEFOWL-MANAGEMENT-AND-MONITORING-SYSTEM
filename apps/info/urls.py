from django.urls import path
from . import views

app_name = 'info'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.info_list_page, name='info_list'),
    path('list/', views.info_list_page, name='info_list_page'),
    path('ajax/list/', views.info_list_ajax, name='info_list_ajax'),
    path('ajax/get/<int:pk>/', views.info_get_ajax, name='info_get_ajax'),
    path('ajax/save/', views.info_save_ajax, name='info_save_ajax'),
    path('ajax/delete/<int:pk>/', views.info_delete_ajax, name='info_delete_ajax'),
    
    # New Endpoints
    path('ajax/health/<int:pk>/', views.health_records_ajax, name='health_records_ajax'),
    path('ajax/health/save/', views.health_record_save_ajax, name='health_record_save_ajax'),
    path('ajax/health/delete/<int:pk>/', views.health_record_delete_ajax, name='health_record_delete_ajax'),
    path('ajax/pedigree/<int:pk>/', views.pedigree_ajax, name='pedigree_ajax'),
    path('export/csv/', views.export_flock_csv, name='export_flock_csv'),
]