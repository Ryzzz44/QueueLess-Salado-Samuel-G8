from django import forms

from .models import Service


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