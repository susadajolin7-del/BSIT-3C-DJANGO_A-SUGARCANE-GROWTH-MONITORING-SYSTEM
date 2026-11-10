from django.urls import path
from . import views, farmer_views

app_name = 'users'

urlpatterns = [
    # Page
    path('', views.user_list_page, name='user_list'),
    # AJAX
    path('ajax/list/', views.user_list_ajax, name='user_list_ajax'),
    path('ajax/get/<int:pk>/', views.user_get_ajax, name='user_get_ajax'),
    path('ajax/save/', views.user_save_ajax, name='user_save_ajax'),
    path('ajax/delete/<int:pk>/', views.user_delete_ajax, name='user_delete_ajax'),

    path('register/', farmer_views.farmer_register, name='farmer_register'),
    path('login/', farmer_views.farmer_login, name='farmer_login'),
    path('dashboard/', farmer_views.farmer_dashboard, name='farmer_dashboard'),
    path('logout/', farmer_views.farmer_logout, name='farmer_logout'),
    path('profile/', farmer_views.farmer_profile, name='farmer_profile'),
    path('fields/', farmer_views.farmer_fields, name='farmer_fields'),
    path('crop-cycles/', farmer_views.farmer_crop_cycles, name='farmer_crop_cycles'),
]
