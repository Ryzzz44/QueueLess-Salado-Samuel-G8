from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'office', 'is_open', 'created_by', 'created_at')
    list_filter = ('is_open', 'office')
    search_fields = ('name', 'code', 'office')