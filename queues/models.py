from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Service(models.Model):
    """A school service students can queue for (e.g. Registrar - Document Request)."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=5,
        unique=True,
        validators=[RegexValidator(r'^[A-Z]{2,5}$', 'Code must be 2 to 5 capital letters (e.g. REG).')],
        help_text='2 to 5 capital letters used as the queue number prefix, e.g. REG → REG-001.',
    )
    office = models.CharField(max_length=100, help_text='Office that handles this service, e.g. Registrar.')
    description = models.TextField(blank=True)
    is_open = models.BooleanField(default=True, help_text='Students can only join services that are open.')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='services_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.code})'