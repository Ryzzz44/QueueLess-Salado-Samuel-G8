from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User

from .forms import JoinQueueForm, ServiceForm, TicketEditForm
from .models import QueueTicket, Service

STAFF = User.Role.STAFF
STUDENT = User.Role.STUDENT


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
        if service.tickets.exists():
            messages.error(
                request,
                f'"{service.name}" already has queue records, so it cannot be deleted. Close it instead.',
            )
            return redirect('service_manage_list')
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


# ---------------------------------------------------------------------------
# Student: join a queue and manage own tickets
# ---------------------------------------------------------------------------

@role_required(STUDENT)
def service_list(request):
    services = Service.objects.filter(is_open=True)
    active_ids = set(
        request.user.queue_tickets.filter(
            queue_date=timezone.localdate(), status__in=QueueTicket.ACTIVE_STATUSES
        ).values_list('service_id', flat=True)
    )
    return render(request, 'queues/service_list.html', {'services': services, 'active_ids': active_ids})


@role_required(STUDENT)
def join_queue(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = JoinQueueForm(request.POST, service=service, student=request.user)
        if form.is_valid():
            with transaction.atomic():
                # Lock the service row so two students never get the same number.
                locked = Service.objects.select_for_update().get(pk=service.pk)
                ticket = form.save(commit=False)
                ticket.service = locked
                ticket.student = request.user
                ticket.queue_date = timezone.localdate()
                ticket.number = locked.next_ticket_number()
                ticket.save()
            messages.success(request, f'You joined the queue! Your number is {ticket.ticket_code}.')
            return redirect('ticket_detail', pk=ticket.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = JoinQueueForm(service=service, student=request.user)
    return render(request, 'queues/join_queue.html', {'form': form, 'service': service})


@role_required(STUDENT)
def my_tickets(request):
    tickets = request.user.queue_tickets.select_related('service')
    active = [t for t in tickets if t.is_active]
    history = [t for t in tickets if not t.is_active]
    return render(request, 'queues/my_tickets.html', {'active': active, 'history': history})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(QueueTicket.objects.select_related('service', 'student'), pk=pk)
    # Students may only see their own tickets; staff may see any ticket.
    if request.user.role != STAFF and ticket.student != request.user:
        raise Http404
    return render(request, 'queues/ticket_detail.html', {'ticket': ticket, 'now_serving': ticket.service.now_serving})


def _own_ticket(request, pk):
    return get_object_or_404(QueueTicket, pk=pk, student=request.user)


@role_required(STUDENT)
def ticket_edit(request, pk):
    ticket = _own_ticket(request, pk)
    if ticket.status != QueueTicket.Status.WAITING or not ticket.is_today:
        messages.error(request, 'You can only edit a ticket that is still waiting.')
        return redirect('ticket_detail', pk=ticket.pk)
    if request.method == 'POST':
        form = TicketEditForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your ticket was updated.')
            return redirect('ticket_detail', pk=ticket.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = TicketEditForm(instance=ticket)
    return render(request, 'queues/ticket_edit.html', {'form': form, 'ticket': ticket})


@role_required(STUDENT)
@require_POST
def ticket_cancel(request, pk):
    ticket = _own_ticket(request, pk)
    if ticket.status != QueueTicket.Status.WAITING or not ticket.is_today:
        messages.error(request, 'Only a waiting ticket can be cancelled.')
    else:
        ticket.status = QueueTicket.Status.CANCELLED
        ticket.finished_at = timezone.now()
        ticket.save(update_fields=['status', 'finished_at'])
        messages.success(request, f'Ticket {ticket.ticket_code} was cancelled.')
    return redirect('my_tickets')


@role_required(STUDENT)
def ticket_delete(request, pk):
    ticket = _own_ticket(request, pk)
    if ticket.is_active:
        messages.error(request, 'You cannot delete an active ticket. Cancel it first.')
        return redirect('ticket_detail', pk=ticket.pk)
    if request.method == 'POST':
        code = ticket.ticket_code
        ticket.delete()
        messages.success(request, f'Ticket {code} was removed from your history.')
        return redirect('my_tickets')
    return render(request, 'queues/ticket_confirm_delete.html', {'ticket': ticket})


# ---------------------------------------------------------------------------
# Staff: run the queue (call next, complete, skip)
# ---------------------------------------------------------------------------

@role_required(STAFF)
def queue_board(request, pk):
    service = get_object_or_404(Service, pk=pk)
    today = service.todays_tickets().select_related('student')
    context = {
        'service': service,
        'now_serving': today.filter(status=QueueTicket.Status.SERVING).first(),
        'waiting': today.filter(status=QueueTicket.Status.WAITING).order_by('number'),
        'done': today.exclude(status__in=QueueTicket.ACTIVE_STATUSES).order_by('-finished_at'),
    }
    return render(request, 'queues/queue_board.html', context)


@role_required(STAFF)
@require_POST
def call_next(request, pk):
    service = get_object_or_404(Service, pk=pk)
    with transaction.atomic():
        Service.objects.select_for_update().get(pk=service.pk)
        if service.now_serving:
            messages.error(request, f'Finish {service.now_serving.ticket_code} first (Complete or Skip).')
            return redirect('queue_board', pk=pk)
        ticket = service.todays_tickets().filter(status=QueueTicket.Status.WAITING).order_by('number').first()
        if not ticket:
            messages.error(request, 'No one is waiting in this queue.')
            return redirect('queue_board', pk=pk)
        ticket.status = QueueTicket.Status.SERVING
        ticket.served_by = request.user
        ticket.called_at = timezone.now()
        ticket.save(update_fields=['status', 'served_by', 'called_at'])
    messages.success(request, f'Now serving {ticket.ticket_code} ({ticket.student.get_full_name() or ticket.student.username}).')
    return redirect('queue_board', pk=pk)


@role_required(STAFF)
@require_POST
def ticket_finish(request, pk, action):
    ticket = get_object_or_404(QueueTicket, pk=pk)
    if action not in ('complete', 'skip'):
        raise Http404
    if ticket.status != QueueTicket.Status.SERVING:
        messages.error(request, 'Only the ticket being served can be completed or skipped.')
    else:
        ticket.status = QueueTicket.Status.COMPLETED if action == 'complete' else QueueTicket.Status.SKIPPED
        ticket.finished_at = timezone.now()
        ticket.save(update_fields=['status', 'finished_at'])
        messages.success(request, f'{ticket.ticket_code} marked as {ticket.get_status_display().lower()}.')
    return redirect('queue_board', pk=ticket.service_id)