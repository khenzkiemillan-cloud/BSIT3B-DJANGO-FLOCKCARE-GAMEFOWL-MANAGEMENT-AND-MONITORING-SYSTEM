from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Count, Q
from django.views.decorators.http import require_POST

from .models import UserProfile
from .forms import UserProfileForm


def _is_superuser(user):
    return user.is_superuser


def _ajax_superuser_required(view_func):
    """Return JSON 403 instead of an HTML redirect when a non-admin calls an AJAX endpoint."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied. Administrator access required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# PAGE
@login_required(login_url='login')
@user_passes_test(_is_superuser, login_url='dashboard')
def user_list_page(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()

    all_users = User.objects.all()
    counts = all_users.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
        admins=Count('id', filter=Q(is_superuser=True)),
        staff=Count('id', filter=Q(is_staff=True, is_superuser=False)),
        regular=Count('id', filter=Q(is_staff=False, is_superuser=False)),
        inactive=Count('id', filter=Q(is_active=False)),
    )

    users_list = all_users.order_by('-date_joined')

    if query:
        users_list = users_list.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if role == 'admin':
        users_list = users_list.filter(is_superuser=True)
    elif role == 'staff':
        users_list = users_list.filter(is_staff=True, is_superuser=False)
    elif role == 'user':
        users_list = users_list.filter(is_staff=False, is_superuser=False)
    elif role == 'inactive':
        users_list = users_list.filter(is_active=False)

    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)

    return render(request, 'users/list.html', {
        'users': users,
        'query': query,
        'role': role,
        'counts': counts,
    })


# LIST USERS (AJAX)
@login_required(login_url='login')
@_ajax_superuser_required
def user_list_ajax(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()

    users_list = User.objects.all().order_by('-date_joined')
    if query:
        users_list = users_list.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    if role == 'admin':
        users_list = users_list.filter(is_superuser=True)
    elif role == 'staff':
        users_list = users_list.filter(is_staff=True, is_superuser=False)
    elif role == 'user':
        users_list = users_list.filter(is_staff=False, is_superuser=False)
    elif role == 'inactive':
        users_list = users_list.filter(is_active=False)

    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)
    data = list(users.object_list.values(
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined',
    ))
    return JsonResponse({
        "data":     data,
        "has_next": users.has_next(),
        "has_prev": users.has_previous(),
        "page":     users.number,
        "pages":    users.paginator.num_pages,
        "total":    users.paginator.count,
    })


# GET SINGLE USER (AJAX)
@login_required(login_url='login')
@_ajax_superuser_required
def user_get_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    return JsonResponse({
        "id":         user.id,
        "username":   user.username,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "email":      user.email,
        "is_staff":   user.is_staff,
        "is_active":  user.is_active,
    })


# CREATE / UPDATE USER (AJAX)
@login_required(login_url='login')
@_ajax_superuser_required
@require_POST
def user_save_ajax(request):
    user_id = request.POST.get("id")

    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return JsonResponse({"error": "User not found."}, status=404)
        is_update = True
    else:
        user = User()
        is_update = False

    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()

    if not username:
        return JsonResponse({"error": "Username is required."}, status=400)

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"error": "Enter a valid email address."}, status=400)

    dup_qs = User.objects.filter(
        Q(username__iexact=username) | (Q(email__iexact=email) & ~Q(email=""))
    )
    if user_id:
        dup_qs = dup_qs.exclude(pk=user_id)
    if dup_qs.filter(username__iexact=username).exists():
        return JsonResponse({"error": "That username is already taken."}, status=400)
    if email and dup_qs.filter(email__iexact=email).exists():
        return JsonResponse({"error": "That email is already in use."}, status=400)

    is_active = request.POST.get("is_active") == "true"
    if user_id and user.pk == request.user.pk and not is_active:
        return JsonResponse({"error": "You cannot deactivate your own account."}, status=400)

    user.username   = username
    user.first_name = request.POST.get("first_name", "").strip()
    user.last_name  = request.POST.get("last_name", "").strip()
    user.email      = email
    user.is_staff   = request.POST.get("is_staff") == "true"
    user.is_active  = is_active

    password = request.POST.get("password")
    if not password and not user_id:
        return JsonResponse({"error": "Password is required for new users."}, status=400)
    if password:
        try:
            validate_password(password, user)
        except ValidationError as exc:
            return JsonResponse({"error": " ".join(exc.messages)}, status=400)
        user.set_password(password)

    try:
        user.save()
    except IntegrityError:
        return JsonResponse({"error": "Could not save user due to a conflict (duplicate username/email)."}, status=400)

    messages.success(
        request,
        f'User "{user.username}" has been {"updated" if is_update else "saved"} successfully.'
    )

    return JsonResponse({
        "status": "success",
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_staff": user.is_staff,
        "is_active": user.is_active,
    })


# DELETE USER (AJAX)
@login_required(login_url='login')
@_ajax_superuser_required
@require_POST
def user_delete_ajax(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user == user:
        return JsonResponse({"error": "You cannot delete yourself"}, status=400)
    username = user.username
    user.delete()
    return JsonResponse({
        "status": "deleted",
        "message": f'User "{username}" has been deleted successfully.',
    })


# USER PROFILE & SETTINGS
@login_required(login_url='login')
def user_profile_page(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        # Update profile info
        profile.farm_name = request.POST.get('farm_name', '').strip()
        profile.contact_number = request.POST.get('contact_number', '').strip()
        profile.location = request.POST.get('location', '').strip()
        profile.association_id = request.POST.get('association_id', '').strip()
        profile.bio = request.POST.get('bio', '').strip()

        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Please enter a valid email address.')
                return render(request, 'users/profile.html', {'profile': profile})

            duplicate = User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists()
            if duplicate:
                messages.error(request, 'That email address is already in use by another account.')
                return render(request, 'users/profile.html', {'profile': profile})
            user.email = email

        user.first_name = first_name
        user.last_name = last_name

        # Password change
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return render(request, 'users/profile.html', {'profile': profile})
            try:
                validate_password(new_password, user)
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
                return render(request, 'users/profile.html', {'profile': profile})
            user.set_password(new_password)
            update_session_auth_hash(request, user)

        user.save()
        profile.save()
        messages.success(request, 'Your profile and farm details have been updated successfully.')
        return redirect('users:profile')

    return render(request, 'users/profile.html', {'profile': profile})
