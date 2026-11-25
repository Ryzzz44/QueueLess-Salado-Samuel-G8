from django.contrib import admin

from .models import QueueTicket, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'office', 'is_open', 'created_by', 'created_at')
    list_filter = ('is_open', 'office')
    search_fields = ('name', 'code', 'office')


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_code', 'service', 'student', 'queue_date', 'status', 'served_by')
    list_filter = ('status', 'service', 'queue_date')
    search_fields = ('student__username', 'purpose')