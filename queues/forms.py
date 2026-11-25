from django import forms

from .models import QueueTicket, Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('name', 'code', 'office', 'description', 'is_open')
        labels = {'is_open': 'Open for queuing'}

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 3:
            raise forms.ValidationError('Service name must be at least 3 characters.')
        if Service.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A service with this name already exists.')
        return name

    def clean_code(self):
        # Accept "reg" and store "REG"; the model validator then checks the format.
        return self.cleaned_data['code'].strip().upper()


class JoinQueueForm(forms.ModelForm):
    class Meta:
        model = QueueTicket
        fields = ('purpose',)

    def __init__(self, *args, service=None, student=None, **kwargs):
        self.service = service
        self.student = student
        super().__init__(*args, **kwargs)

    def clean_purpose(self):
        purpose = self.cleaned_data['purpose'].strip()
        if len(purpose) < 5:
            raise forms.ValidationError('Please describe your purpose in at least 5 characters.')
        return purpose

    def clean(self):
        cleaned = super().clean()
        if self.service and not self.service.is_open:
            raise forms.ValidationError('This service is currently closed. Please try again later.')
        if self.service and self.student:
            already = self.service.todays_tickets().filter(
                student=self.student, status__in=QueueTicket.ACTIVE_STATUSES
            ).exists()
            if already:
                raise forms.ValidationError('You already have an active ticket for this service today.')
        return cleaned


class TicketEditForm(forms.ModelForm):
    class Meta:
        model = QueueTicket
        fields = ('purpose',)

    def clean_purpose(self):
        purpose = self.cleaned_data['purpose'].strip()
        if len(purpose) < 5:
            raise forms.ValidationError('Please describe your purpose in at least 5 characters.')
        return purpose