from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from apps.core.scoping import scoped_flock_members
from apps.info.models import HealthRecord

User = get_user_model()
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION = timedelta(minutes=1)
INVALID_LOGIN_MESSAGE = 'Invalid username or password.'
LOCKED_MESSAGE = 'Too many failed attempts. Locked for 1 minute.'


def _reset_lock_state(request):
    request.session['failed_attempts'] = 0
    request.session['lock_time'] = None


def _safe_next_url(request):
    """Return a validated same-host ``next`` URL, or ``None``."""
    candidate = request.POST.get('next') or request.GET.get('next')
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return None


def _get_lock_state(request):
    failed_attempts = request.session.get('failed_attempts', 0)
    lock_time = request.session.get('lock_time')

    if not lock_time:
        return failed_attempts, None

    try:
        unlock_time = timezone.datetime.fromisoformat(lock_time)
    except (TypeError, ValueError):
        _reset_lock_state(request)
        return 0, None

    if timezone.now() < unlock_time:
        remaining = int((unlock_time - timezone.now()).total_seconds())
        return failed_attempts, remaining

    _reset_lock_state(request)
    return 0, None


def _set_lock_state(request):
    lock_until = timezone.now() + LOCK_DURATION
    request.session['failed_attempts'] = MAX_FAILED_ATTEMPTS
    request.session['lock_time'] = lock_until.isoformat()
    return int(LOCK_DURATION.total_seconds())


def _validate_registration_data(data):
    errors = {}

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username:
        errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already taken.'

    if not first_name:
        errors['first_name'] = 'First name is required.'

    if not last_name:
        errors['last_name'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email is required.'
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors['email'] = 'Enter a valid email address.'
        else:
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

    if not password:
        errors['password'] = 'Password is required.'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors['password'] = ' '.join(exc.messages)

    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match.'

    return errors


@require_http_methods(['GET', 'POST'])
def login_view(request):
    next_url = _safe_next_url(request)

    if request.user.is_authenticated:
        return redirect(next_url or 'dashboard')

    failed_attempts, remaining = _get_lock_state(request)
    if remaining is not None:
        messages.error(request, f'Too many failed attempts. Try again in {remaining} seconds.')
        return render(request, 'auth/login.html', {
            'locked': True,
            'remaining': remaining,
            'next': next_url,
        })

    if request.method == 'GET':
        return render(request, 'auth/login.html', {'next': next_url})

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        _reset_lock_state(request)
        login(request, user)
        return redirect(next_url or 'dashboard')

    failed_attempts += 1
    request.session['failed_attempts'] = failed_attempts
    if failed_attempts >= MAX_FAILED_ATTEMPTS:
        remaining = _set_lock_state(request)
        messages.error(request, LOCKED_MESSAGE)
        return render(request, 'auth/login.html', {
            'locked': True,
            'remaining': remaining,
            'next': next_url,
        })

    remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
    messages.error(request, f'{INVALID_LOGIN_MESSAGE} {remaining_attempts} attempts remaining.')
    return render(request, 'auth/login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home(request):
    """Render the flock dashboard with live statistics and reminders."""
    members = scoped_flock_members(request.user)
    today = timezone.localdate()
    upcoming_cutoff = today + timedelta(days=30)

    stats = members.aggregate(
        total_birds=Count('id'),
        active_birds=Count('id', filter=Q(status='Active')),
        conditioning_birds=Count('id', filter=Q(status='Conditioning')),
        retired_birds=Count('id', filter=Q(status='Retired')),
        total_wins=Sum('wins'),
        total_losses=Sum('losses'),
    )
    total_birds = stats['total_birds'] or 0
    active_birds = stats['active_birds'] or 0
    conditioning_birds = stats['conditioning_birds'] or 0
    retired_birds = stats['retired_birds'] or 0
    total_wins = stats['total_wins'] or 0
    total_losses = stats['total_losses'] or 0
    total_fights = total_wins + total_losses
    win_rate = round(total_wins / total_fights * 100) if total_fights else 0

    def _pct(value):
        return round(value / total_birds * 100) if total_birds else 0

    other_birds = max(total_birds - active_birds - conditioning_birds - retired_birds, 0)
    active_pct = _pct(active_birds)
    conditioning_pct = _pct(conditioning_birds)
    retired_pct = _pct(retired_birds)

    upcoming_qs = HealthRecord.objects.filter(
        bird__in=members,
        next_due_date__isnull=False,
        next_due_date__gte=today,
        next_due_date__lte=upcoming_cutoff,
    )
    upcoming_records = upcoming_qs.select_related('bird').order_by('next_due_date')[:5]

    overdue_qs = HealthRecord.objects.filter(
        bird__in=members,
        next_due_date__isnull=False,
        next_due_date__lt=today,
    )
    overdue_records = overdue_qs.select_related('bird').order_by('next_due_date')[:5]

    context = {
        'total_birds': total_birds,
        'active_birds': active_birds,
        'conditioning_birds': conditioning_birds,
        'retired_birds': retired_birds,
        'active_pct': active_pct,
        'conditioning_pct': conditioning_pct,
        'retired_pct': retired_pct,
        'other_birds': other_birds,
        'other_pct': max(100 - active_pct - conditioning_pct - retired_pct, 0),
        'breed_count': members.exclude(breed__isnull=True).values('breed').distinct().count(),
        'total_wins': total_wins,
        'total_losses': total_losses,
        'total_fights': total_fights,
        'win_rate': win_rate,
        'recent_members': members.select_related('breed').order_by('-created_at')[:5],
        'upcoming_records': upcoming_records,
        'upcoming_count': upcoming_qs.count(),
        'overdue_records': overdue_records,
        'overdue_count': overdue_qs.count(),
        'today': today,
    }
    return render(request, 'home.html', context)


@require_http_methods(['GET', 'POST'])
def register_view(request):
    next_url = _safe_next_url(request)

    if request.user.is_authenticated:
        return redirect(next_url or 'dashboard')

    if request.method == 'GET':
        return render(request, 'auth/register.html', {'next': next_url})

    form_data = {
        'username': request.POST.get('username', ''),
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'email': request.POST.get('email', ''),
        'password': request.POST.get('password', ''),
        'confirm_password': request.POST.get('confirm_password', ''),
    }

    errors = _validate_registration_data(form_data)
    if errors:
        return render(request, 'auth/register.html', {
            'errors': errors,
            'form_data': form_data,
            'next': next_url,
        })

    user = User.objects.create_user(
        username=form_data['username'].strip(),
        first_name=form_data['first_name'].strip(),
        last_name=form_data['last_name'].strip(),
        email=form_data['email'].strip(),
        password=form_data['password'],
    )
    login(request, user)
    return redirect(next_url or 'dashboard')
