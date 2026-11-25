from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from queues.models import QueueTicket, Service

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their role."""
    if request.user.role == User.Role.STAFF:
        return redirect('staff_dashboard')
    return redirect('student_dashboard')


@role_required(User.Role.STUDENT)
def student_dashboard(request):
    tickets = request.user.queue_tickets.select_related('service')
    active = [t for t in tickets if t.is_active]
    context = {
        'active_tickets': active,
        'open_services': Service.objects.filter(is_open=True).count(),
        'completed_count': tickets.filter(status=QueueTicket.Status.COMPLETED).count(),
    }
    return render(request, 'accounts/student_dashboard.html', context)


@role_required(User.Role.STAFF)
def staff_dashboard(request):
    today = QueueTicket.objects.filter(queue_date=timezone.localdate())
    context = {
        'student_count': User.objects.filter(role=User.Role.STUDENT).count(),
        'services': Service.objects.all(),
        'waiting_today': today.filter(status=QueueTicket.Status.WAITING).count(),
        'served_today': today.filter(status=QueueTicket.Status.COMPLETED).count(),
    }
    return render(request, 'accounts/staff_dashboard.html', context)


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'profile_user': request.user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})