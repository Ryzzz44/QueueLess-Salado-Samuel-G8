from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms import ServiceForm
from .models import Service

STAFF = User.Role.STAFF


def _redirect_back(request, fallback, *args):
    """Go back to the page the form came from, but only if it is on this site."""
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect(fallback, *args)


# ---------------------------------------------------------------------------
# Staff: manage services (Create / Read / Update / Delete)
# ---------------------------------------------------------------------------

@role_required(STAFF)
def service_manage_list(request):
    services = Service.objects.all()
    return render(request, 'queues/service_manage_list.html', {'services': services})


@role_required(STAFF)
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.created_by = request.user
            service.save()
            messages.success(request, f'Service "{service.name}" was created.')
            return redirect('service_manage_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceForm()
    return render(request, 'queues/service_form.html', {'form': form, 'title': 'Add Service'})


@role_required(STAFF)
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f'Service "{service.name}" was updated.')
            return redirect('service_manage_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'queues/service_form.html', {'form': form, 'title': 'Edit Service', 'service': service})


@role_required(STAFF)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        name = service.name
        service.delete()
        messages.success(request, f'Service "{name}" was deleted.')
        return redirect('service_manage_list')
    return render(request, 'queues/service_confirm_delete.html', {'service': service})


@role_required(STAFF)
@require_POST
def service_toggle(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.is_open = not service.is_open
    service.save(update_fields=['is_open', 'updated_at'])
    state = 'opened' if service.is_open else 'closed'
    messages.success(request, f'"{service.name}" is now {state}.')
    return _redirect_back(request, 'service_manage_list')