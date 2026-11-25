from django.urls import path

from . import views

urlpatterns = [
    # Staff: services CRUD
    path('staff/services/', views.service_manage_list, name='service_manage_list'),
    path('staff/services/add/', views.service_create, name='service_create'),
    path('staff/services/<int:pk>/edit/', views.service_update, name='service_update'),
    path('staff/services/<int:pk>/delete/', views.service_delete, name='service_delete'),
    path('staff/services/<int:pk>/toggle/', views.service_toggle, name='service_toggle'),
    # Staff: run a queue
    path('staff/services/<int:pk>/queue/', views.queue_board, name='queue_board'),
    path('staff/services/<int:pk>/call-next/', views.call_next, name='call_next'),
    path('staff/tickets/<int:pk>/<str:action>/', views.ticket_finish, name='ticket_finish'),
    # Student: join and manage tickets
    path('services/', views.service_list, name='service_list'),
    path('services/<int:pk>/join/', views.join_queue, name='join_queue'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/edit/', views.ticket_edit, name='ticket_edit'),
    path('tickets/<int:pk>/cancel/', views.ticket_cancel, name='ticket_cancel'),
    path('tickets/<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
]