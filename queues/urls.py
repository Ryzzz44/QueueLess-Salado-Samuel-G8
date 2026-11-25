from django.urls import path

from . import views

urlpatterns = [
    # Staff: services CRUD
    path('staff/services/', views.service_manage_list, name='service_manage_list'),
    path('staff/services/add/', views.service_create, name='service_create'),
    path('staff/services/<int:pk>/edit/', views.service_update, name='service_update'),
    path('staff/services/<int:pk>/delete/', views.service_delete, name='service_delete'),
    path('staff/services/<int:pk>/toggle/', views.service_toggle, name='service_toggle'),
]