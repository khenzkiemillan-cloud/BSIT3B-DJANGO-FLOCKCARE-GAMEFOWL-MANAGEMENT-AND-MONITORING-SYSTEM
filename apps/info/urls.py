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

    # Fight Records
    path('ajax/fight/<int:pk>/', views.fight_records_ajax, name='fight_records_ajax'),
    path('ajax/fight/save/', views.fight_record_save_ajax, name='fight_record_save_ajax'),
    path('ajax/fight/delete/<int:pk>/', views.fight_record_delete_ajax, name='fight_record_delete_ajax'),

    # Weight / Conditioning Logs
    path('ajax/weight/<int:pk>/', views.weight_logs_ajax, name='weight_logs_ajax'),
    path('ajax/weight/save/', views.weight_log_save_ajax, name='weight_log_save_ajax'),
    path('ajax/weight/delete/<int:pk>/', views.weight_log_delete_ajax, name='weight_log_delete_ajax'),

    # Breeding Pens & Clutches
    path('breeding/', views.breeding_list_page, name='breeding_list'),
    path('ajax/breeding/save/', views.breeding_pen_save_ajax, name='breeding_pen_save_ajax'),
    path('ajax/breeding/delete/<int:pk>/', views.breeding_pen_delete_ajax, name='breeding_pen_delete_ajax'),
    path('ajax/clutch/save/', views.clutch_save_ajax, name='clutch_save_ajax'),

    # Pedigree & Certificate
    path('ajax/pedigree/<int:pk>/', views.pedigree_ajax, name='pedigree_ajax'),
    path('pedigree/<int:pk>/certificate/', views.pedigree_certificate_page, name='pedigree_certificate'),

    # Health and care schedule
    path('ajax/health/<int:pk>/', views.health_records_ajax, name='health_records_ajax'),
    path('ajax/health/save/', views.health_record_save_ajax, name='health_record_save_ajax'),
    path('ajax/health/delete/<int:pk>/', views.health_record_delete_ajax, name='health_record_delete_ajax'),
    path('health/', views.health_list_page, name='health_list'),
    path('health/export/csv/', views.export_health_csv, name='export_health_csv'),

    # Medicine cabinet
    path('medicines/', views.medicine_list_page, name='medicine_list'),
    path('medicines/export/csv/', views.export_medicines_csv, name='export_medicines_csv'),
    path('ajax/medicines/save/', views.medicine_save_ajax, name='medicine_save_ajax'),
    path('ajax/medicines/delete/<int:pk>/', views.medicine_delete_ajax, name='medicine_delete_ajax'),
    path('ajax/medicines/restock/', views.medicine_restock_ajax, name='medicine_restock_ajax'),

    # CSV Import / Export & Batch Actions
    path('export/csv/', views.export_flock_csv, name='export_flock_csv'),
    path('import/csv/', views.import_flock_csv, name='import_flock_csv'),
    path('ajax/batch/', views.flock_batch_action_ajax, name='batch_action_ajax'),
]
