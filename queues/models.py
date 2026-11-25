from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


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
    # Daily ticket counter: numbers are never reused, even if a ticket is deleted.
    last_ticket_number = models.PositiveIntegerField(default=0, editable=False)
    last_ticket_date = models.DateField(null=True, blank=True, editable=False)
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

    def todays_tickets(self):
        return self.tickets.filter(queue_date=timezone.localdate())

    def next_ticket_number(self):
        """Give out the next number for today. Call inside a transaction on a locked row."""
        today = timezone.localdate()
        if self.last_ticket_date != today:
            self.last_ticket_date = today
            self.last_ticket_number = 0
        # Never go below a number already handed out today (safety for existing data).
        highest = self.tickets.filter(queue_date=today).aggregate(m=models.Max('number'))['m'] or 0
        self.last_ticket_number = max(self.last_ticket_number, highest) + 1
        self.save(update_fields=['last_ticket_number', 'last_ticket_date'])
        return self.last_ticket_number

    @property
    def waiting_count(self):
        return self.todays_tickets().filter(status=QueueTicket.Status.WAITING).count()

    @property
    def now_serving(self):
        return self.todays_tickets().filter(status=QueueTicket.Status.SERVING).first()


class QueueTicket(models.Model):
    """A student's place in a service's queue for one day."""

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        SERVING = 'SERVING', 'Now Serving'
        COMPLETED = 'COMPLETED', 'Completed'
        SKIPPED = 'SKIPPED', 'Skipped'
        CANCELLED = 'CANCELLED', 'Cancelled'

    ACTIVE_STATUSES = [Status.WAITING, Status.SERVING]

    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='tickets')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='queue_tickets')
    number = models.PositiveIntegerField()
    queue_date = models.DateField(default=timezone.localdate)
    purpose = models.CharField(max_length=200, help_text='What do you need? e.g. "Request copy of TOR".')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.WAITING)
    served_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_served',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-queue_date', 'service', 'number']
        constraints = [
            models.UniqueConstraint(fields=['service', 'queue_date', 'number'], name='unique_ticket_number_per_service_per_day'),
        ]

    def __str__(self):
        return f'{self.ticket_code} - {self.student.username}'

    @property
    def ticket_code(self):
        return f'{self.service.code}-{self.number:03d}'

    @property
    def is_today(self):
        return self.queue_date == timezone.localdate()

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES and self.is_today

    @property
    def is_expired(self):
        return self.status in self.ACTIVE_STATUSES and not self.is_today

    @property
    def position(self):
        """1 = next in line. None if the ticket is not waiting."""
        if self.status != self.Status.WAITING or not self.is_today:
            return None
        ahead = QueueTicket.objects.filter(
            service=self.service,
            queue_date=self.queue_date,
            status=self.Status.WAITING,
            number__lt=self.number,
        ).count()
        return ahead + 1

    @property
    def status_badge(self):
        if self.is_expired:
            return 'secondary'
        return {
            'WAITING': 'warning',
            'SERVING': 'success',
            'COMPLETED': 'primary',
            'SKIPPED': 'danger',
            'CANCELLED': 'secondary',
        }[self.status]

    @property
    def status_label(self):
        return 'Expired' if self.is_expired else self.get_status_display()