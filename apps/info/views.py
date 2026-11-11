import csv
import io
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.scoping import scoped_flock_member, scoped_flock_members
from .forms import (
    FlockMemberForm, HealthRecordForm, MedicineForm,
    FightRecordForm, WeightLogForm, BreedingPenForm, ClutchRecordForm
)
from .models import (
    Breed, FlockMember, HealthRecord, Medicine,
    FightRecord, WeightLog, BreedingPen, ClutchRecord
)

HEALTH_DUE_WINDOW_DAYS = 30
MEDICINE_EXPIRY_WINDOW_DAYS = 30


def _form_error_message(form):
    """Return the first human-readable validation error from a form."""
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return 'Please correct the highlighted fields.'


def _json_not_found(view_func):
    """Turn a missing record into a JSON 404 instead of an HTML error page."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Http404:
            return JsonResponse({'error': 'Record not found.'}, status=404)

    return wrapper


def _resolve_breed(form, request):
    """Resolve the selected breed, creating one when a new name is supplied."""
    new_breed = (request.POST.get('new_breed') or '').strip()
    if not new_breed:
        return form.cleaned_data.get('breed'), None

    if len(new_breed) > 100:
        return None, 'Breed name must be 100 characters or fewer.'

    breed = Breed.objects.filter(name__iexact=new_breed).first()
    if breed is None:
        breed = Breed.objects.create(name=new_breed)
    return breed, None


@login_required(login_url='login')
def dashboard_view(request):
    """Send the flock dashboard to the project's main dashboard."""
    return redirect('dashboard')


@login_required(login_url='login')
def info_list_page(request):
    """Render searchable, paginated flock member list."""
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    gender = request.GET.get('gender', '').strip()
    breed_id = request.GET.get('breed', '').strip()

    all_members = scoped_flock_members(request.user)
    counts = all_members.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='Active')),
        conditioning=Count('id', filter=Q(status='Conditioning')),
        retired=Count('id', filter=Q(status='Retired')),
        breeding=Count('id', filter=Q(status__in=['Broodcock', 'Broodhen'])),
    )

    members_list = all_members.select_related('breed').order_by('-created_at')

    if query:
        members_list = members_list.filter(
            Q(tag_number__icontains=query) |
            Q(breed__name__icontains=query) |
            Q(gender__icontains=query) |
            Q(status__icontains=query) |
            Q(sire__icontains=query) |
            Q(dam__icontains=query) |
            Q(color__icontains=query) |
            Q(cage_number__icontains=query)
        )

    if status == 'breeding':
        members_list = members_list.filter(status__in=['Broodcock', 'Broodhen'])
    elif status:
        members_list = members_list.filter(status=status)

    if gender:
        members_list = members_list.filter(gender=gender)

    if breed_id and breed_id.isdigit():
        members_list = members_list.filter(breed_id=int(breed_id))

    paginator = Paginator(members_list, 10)
    page_number = request.GET.get('page', 1)
    members = paginator.get_page(page_number)
    breeds = Breed.objects.all()

    return render(request, 'info/info_list.html', {
        'members': members,
        'breeds': breeds,
        'query': query,
        'status': status,
        'gender': gender,
        'breed_id': breed_id,
        'counts': counts,
    })


@login_required(login_url='login')
def info_list_ajax(request):
    """Return the filtered flock member list as JSON for AJAX consumers."""
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    members_list = scoped_flock_members(request.user).select_related('breed').order_by('-created_at')
    if query:
        members_list = members_list.filter(
            Q(tag_number__icontains=query) |
            Q(breed__name__icontains=query) |
            Q(gender__icontains=query) |
            Q(status__icontains=query) |
            Q(sire__icontains=query) |
            Q(dam__icontains=query) |
            Q(color__icontains=query) |
            Q(cage_number__icontains=query)
        )
    if status == 'breeding':
        members_list = members_list.filter(status__in=['Broodcock', 'Broodhen'])
    elif status:
        members_list = members_list.filter(status=status)

    paginator = Paginator(members_list, 10)
    page = paginator.get_page(request.GET.get('page', 1))
    data = [{
        'id': bird.id,
        'tag_number': bird.tag_number,
        'breed': bird.breed.name if bird.breed else '',
        'gender': bird.gender,
        'status': bird.status,
        'weight_grams': bird.weight_grams,
        'wins': bird.wins,
        'losses': bird.losses,
        'draws': bird.draws,
        'cage_number': bird.cage_number,
        'image_url': bird.image.url if bird.image else '',
    } for bird in page.object_list]
    return JsonResponse({
        'data': data,
        'has_next': page.has_next(),
        'has_prev': page.has_previous(),
        'page': page.number,
        'pages': paginator.num_pages,
        'total': paginator.count,
    })


@login_required(login_url='login')
@_json_not_found
def info_get_ajax(request, pk):
    """Retrieve details of a single flock member via AJAX."""
    bird = scoped_flock_member(request.user, pk)
    return JsonResponse({
        'id': bird.id,
        'tag_number': bird.tag_number,
        'breed_id': bird.breed.id if bird.breed else None,
        'gender': bird.gender,
        'birth_date': str(bird.birth_date) if bird.birth_date else '',
        'sire': bird.sire or '',
        'dam': bird.dam or '',
        'status': bird.status,
        'comb_type': bird.comb_type,
        'leg_color': bird.leg_color,
        'color': bird.color or '',
        'cage_number': bird.cage_number or '',
        'weight_grams': bird.weight_grams,
        'wins': bird.wins,
        'losses': bird.losses,
        'draws': bird.draws,
        'image_url': bird.image.url if bird.image else '',
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def info_save_ajax(request):
    """Create or update a flock member record."""
    info_id = (request.POST.get('id') or '').strip()

    if info_id:
        bird = scoped_flock_member(request.user, info_id)
    else:
        bird = FlockMember(user=request.user)

    form = FlockMemberForm(request.POST, request.FILES, instance=bird, user=request.user)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    breed, breed_error = _resolve_breed(form, request)
    if breed_error:
        return JsonResponse({'error': breed_error}, status=400)

    bird = form.save(commit=False)
    bird.user = request.user
    bird.breed = breed
    bird.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Flock member saved successfully.',
        'id': bird.pk,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def info_delete_ajax(request, pk):
    """Delete a flock member record via AJAX."""
    bird = scoped_flock_member(request.user, pk)
    tag_number = bird.tag_number
    bird.delete()
    return JsonResponse({
        'status': 'success',
        'message': f'Flock member "{tag_number}" deleted successfully.',
    })


# --- FIGHT & PERFORMANCE RECORDS ---

@login_required(login_url='login')
@_json_not_found
def fight_records_ajax(request, pk):
    """Retrieve all fight/match records for a bird."""
    bird = scoped_flock_member(request.user, pk)
    fights = bird.fight_records.order_by('-fight_date', '-created_at')
    data = [{
        'id': f.id,
        'event_name': f.event_name,
        'fight_date': str(f.fight_date),
        'weight_grams': f.weight_grams or '',
        'opponent': f.opponent or '',
        'gaff_type': f.gaff_type or '',
        'result': f.result,
        'result_display': f.get_result_display(),
        'duration_seconds': f.duration_seconds or '',
        'video_url': f.video_url or '',
        'notes': f.notes or '',
    } for f in fights]
    return JsonResponse({
        'bird_tag': bird.tag_number,
        'wins': bird.wins,
        'losses': bird.losses,
        'draws': bird.draws,
        'win_rate': bird.win_rate,
        'data': data
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def fight_record_save_ajax(request):
    """Create or update a fight/match record and sync counters."""
    record_id = (request.POST.get('record_id') or '').strip()
    bird_id = (request.POST.get('bird_id') or '').strip()
    if not bird_id:
        return JsonResponse({'error': 'Please select a bird.'}, status=400)
    bird = scoped_flock_member(request.user, bird_id)

    if record_id:
        if not record_id.isdigit():
            raise Http404('Fight record not found.')
        record = FightRecord.objects.filter(pk=record_id, bird__user=request.user).first()
        if record is None:
            raise Http404('Fight record not found.')
    else:
        record = None

    form = FightRecordForm(request.POST, instance=record)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    record = form.save(commit=False)
    record.bird = bird
    record.save()

    # Recalculate bird counters
    bird.wins = bird.fight_records.filter(result='win').count()
    bird.losses = bird.fight_records.filter(result='loss').count()
    bird.draws = bird.fight_records.filter(result='draw').count()
    bird.save(update_fields=['wins', 'losses', 'draws'])

    return JsonResponse({
        'status': 'success',
        'message': 'Fight record saved successfully.',
        'id': record.pk,
        'wins': bird.wins,
        'losses': bird.losses,
        'draws': bird.draws,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def fight_record_delete_ajax(request, pk):
    """Delete a fight record and update bird counters."""
    record = FightRecord.objects.filter(pk=pk, bird__user=request.user).first()
    if record is None:
        raise Http404('Fight record not found.')
    bird = record.bird
    record.delete()

    bird.wins = bird.fight_records.filter(result='win').count()
    bird.losses = bird.fight_records.filter(result='loss').count()
    bird.draws = bird.fight_records.filter(result='draw').count()
    bird.save(update_fields=['wins', 'losses', 'draws'])

    return JsonResponse({
        'status': 'success',
        'message': 'Fight record deleted successfully.',
    })


# --- CONDITIONING & WEIGHT LOGS ---

@login_required(login_url='login')
@_json_not_found
def weight_logs_ajax(request, pk):
    """Retrieve conditioning weight curve logs for a bird."""
    bird = scoped_flock_member(request.user, pk)
    logs = bird.weight_logs.order_by('date', 'created_at')
    data = [{
        'id': log.id,
        'date': str(log.date),
        'time_of_day': log.time_of_day,
        'time_display': log.get_time_of_day_display(),
        'weight_grams': log.weight_grams,
        'notes': log.notes or '',
    } for log in logs]
    return JsonResponse({
        'bird_tag': bird.tag_number,
        'current_weight': bird.weight_grams,
        'data': data
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def weight_log_save_ajax(request):
    """Log bird morning or evening weight."""
    bird_id = (request.POST.get('bird_id') or '').strip()
    bird = scoped_flock_member(request.user, bird_id)

    form = WeightLogForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    log = form.save(commit=False)
    log.bird = bird
    log.save()

    # Update latest bird weight
    bird.weight_grams = log.weight_grams
    bird.save(update_fields=['weight_grams'])

    return JsonResponse({
        'status': 'success',
        'message': f'Logged {log.weight_grams}g on {log.date}.',
        'weight_grams': log.weight_grams,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def weight_log_delete_ajax(request, pk):
    """Delete a weight log."""
    log = WeightLog.objects.filter(pk=pk, bird__user=request.user).first()
    if log is None:
        raise Http404('Weight log not found.')
    log.delete()
    return JsonResponse({'status': 'success', 'message': 'Weight log deleted.'})


# --- BREEDING & CLUTCH VIEWS ---

@login_required(login_url='login')
def breeding_list_page(request):
    """Render breeding pens and clutch hatch tracking."""
    pens = BreedingPen.objects.filter(user=request.user).select_related('sire', 'dam').prefetch_related('clutches')
    members = scoped_flock_members(request.user)
    cocks = members.filter(gender__in=['Cock', 'Stag'])
    hens = members.filter(gender__in=['Hen', 'Pullet'])

    return render(request, 'info/breeding_list.html', {
        'pens': pens,
        'cocks': cocks,
        'hens': hens,
    })


@login_required(login_url='login')
@require_POST
def breeding_pen_save_ajax(request):
    """Create or update a breeding pen pairing."""
    pen_id = (request.POST.get('id') or '').strip()
    if pen_id:
        pen = BreedingPen.objects.filter(pk=pen_id, user=request.user).first()
        if not pen:
            return JsonResponse({'error': 'Breeding pen not found.'}, status=404)
    else:
        pen = BreedingPen(user=request.user)

    form = BreedingPenForm(request.POST, instance=pen)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    pen = form.save(commit=False)
    pen.user = request.user
    pen.save()

    return JsonResponse({'status': 'success', 'message': 'Breeding pen saved.'})


@login_required(login_url='login')
@require_POST
def breeding_pen_delete_ajax(request, pk):
    """Delete a breeding pen."""
    pen = BreedingPen.objects.filter(pk=pk, user=request.user).first()
    if not pen:
        return JsonResponse({'error': 'Pen not found.'}, status=404)
    pen.delete()
    return JsonResponse({'status': 'success', 'message': 'Breeding pen deleted.'})


@login_required(login_url='login')
@require_POST
def clutch_save_ajax(request):
    """Log egg clutch and hatch progress."""
    pen_id = (request.POST.get('pen_id') or '').strip()
    pen = BreedingPen.objects.filter(pk=pen_id, user=request.user).first()
    if not pen:
        return JsonResponse({'error': 'Breeding pen not found.'}, status=404)

    clutch_id = (request.POST.get('clutch_id') or '').strip()
    clutch = ClutchRecord.objects.filter(pk=clutch_id, pen=pen).first() if clutch_id else None

    form = ClutchRecordForm(request.POST, instance=clutch)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    clutch = form.save(commit=False)
    clutch.pen = pen
    clutch.save()

    return JsonResponse({'status': 'success', 'message': 'Clutch record saved.'})


# --- HEALTH RECORD VIEWS ---

@login_required(login_url='login')
@_json_not_found
def health_records_ajax(request, pk):
    """Retrieve all health records for a specific bird."""
    bird = scoped_flock_member(request.user, pk)
    records = bird.health_records.order_by('-date_administered')
    data = [{
        'id': record.id,
        'record_type': record.record_type,
        'title': record.title,
        'date_administered': str(record.date_administered),
        'next_due_date': str(record.next_due_date) if record.next_due_date else '',
        'notes': record.notes or '',
    } for record in records]
    return JsonResponse({'bird_tag': bird.tag_number, 'data': data})


@login_required(login_url='login')
@require_POST
@_json_not_found
def health_record_save_ajax(request):
    """Create or update a health or vaccination log."""
    record_id = (request.POST.get('record_id') or '').strip()
    bird_id = (request.POST.get('bird_id') or '').strip()
    if not bird_id:
        return JsonResponse({'error': 'Please select a bird.'}, status=400)
    bird = scoped_flock_member(request.user, bird_id)

    if record_id:
        if not record_id.isdigit():
            raise Http404('Health record not found.')
        record = HealthRecord.objects.filter(pk=record_id, bird__user=request.user).first()
        if record is None:
            raise Http404('Health record not found.')
    else:
        record = None

    form = HealthRecordForm(request.POST, instance=record)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    record = form.save(commit=False)
    record.bird = bird
    record.save()

    return JsonResponse({
        'status': 'success',
        'message': (
            'Health record updated successfully.' if record_id
            else 'Health record added successfully.'
        ),
        'id': record.pk,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def health_record_delete_ajax(request, pk):
    """Delete a health record that belongs to one of the user's birds."""
    record = HealthRecord.objects.filter(pk=pk, bird__user=request.user).first()
    if record is None:
        raise Http404('Health record not found.')

    title = record.title
    record.delete()
    return JsonResponse({
        'status': 'success',
        'message': f'Health record "{title}" deleted successfully.',
    })


# --- HEALTH DASHBOARD ---

@login_required(login_url='login')
def health_list_page(request):
    """Render the health and care schedule for the user's flock."""
    today = timezone.localdate()
    due_cutoff = today + timedelta(days=HEALTH_DUE_WINDOW_DAYS)
    query = request.GET.get('q', '').strip()
    state = request.GET.get('state', '').strip()
    record_type = request.GET.get('record_type', '').strip()

    records = HealthRecord.objects.filter(bird__user=request.user).select_related('bird')
    counts = records.aggregate(
        total=Count('id'),
        overdue=Count('id', filter=Q(next_due_date__lt=today)),
        due_soon=Count('id', filter=Q(
            next_due_date__gte=today,
            next_due_date__lte=due_cutoff,
        )),
        scheduled=Count('id', filter=Q(next_due_date__isnull=False)),
        unscheduled=Count('id', filter=Q(next_due_date__isnull=True)),
        birds_covered=Count('bird', distinct=True),
    )

    if query:
        records = records.filter(
            Q(bird__tag_number__icontains=query) |
            Q(title__icontains=query) |
            Q(record_type__icontains=query) |
            Q(notes__icontains=query)
        )

    if record_type:
        records = records.filter(record_type=record_type)

    if state == 'overdue':
        records = records.filter(next_due_date__lt=today)
    elif state == 'upcoming':
        records = records.filter(
            next_due_date__gte=today,
            next_due_date__lte=due_cutoff,
        )
    elif state == 'scheduled':
        records = records.filter(next_due_date__isnull=False)
    elif state == 'unscheduled':
        records = records.filter(next_due_date__isnull=True)

    records = records.order_by(
        F('next_due_date').asc(nulls_last=True),
        '-date_administered',
        '-created_at',
    )

    paginator = Paginator(records, 15)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'info/health_list.html', {
        'records': page,
        'birds': scoped_flock_members(request.user).order_by('tag_number'),
        'record_types': HealthRecord.RECORD_TYPES,
        'query': query,
        'state': state,
        'record_type': record_type,
        'counts': counts,
        'today': today,
        'due_cutoff': due_cutoff,
        'due_window_days': HEALTH_DUE_WINDOW_DAYS,
    })


@login_required(login_url='login')
def export_health_csv(request):
    """Export the user's health and treatment records as a CSV file."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="health_records.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Bird Tag',
        'Record Type',
        'Title',
        'Date Administered',
        'Next Due Date',
        'Notes',
    ])

    records = HealthRecord.objects.filter(
        bird__user=request.user,
    ).select_related('bird').order_by('-date_administered', '-created_at')

    for record in records:
        writer.writerow([
            record.bird.tag_number,
            record.record_type,
            record.title,
            record.date_administered,
            record.next_due_date or '',
            record.notes or '',
        ])

    return response


# --- MEDICINE CABINET ---

@login_required(login_url='login')
def medicine_list_page(request):
    """Render the medicine cabinet with stock and expiry information."""
    today = timezone.localdate()
    expiry_cutoff = today + timedelta(days=MEDICINE_EXPIRY_WINDOW_DAYS)
    query = request.GET.get('q', '').strip()
    state = request.GET.get('state', '').strip()
    category = request.GET.get('category', '').strip()

    medicines = Medicine.objects.filter(user=request.user)
    counts = medicines.aggregate(
        total=Count('id'),
        low_stock=Count('id', filter=Q(
            stock_quantity__gt=0,
            stock_quantity__lte=F('low_stock_threshold'),
        )),
        out_of_stock=Count('id', filter=Q(stock_quantity__lte=0)),
        expiring=Count('id', filter=Q(
            expiration_date__gte=today,
            expiration_date__lte=expiry_cutoff,
        )),
        expired=Count('id', filter=Q(expiration_date__lt=today)),
    )

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(notes__icontains=query)
        )

    if category:
        medicines = medicines.filter(category=category)

    if state == 'low':
        medicines = medicines.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('low_stock_threshold'),
        )
    elif state == 'out':
        medicines = medicines.filter(stock_quantity__lte=0)
    elif state == 'expiring':
        medicines = medicines.filter(
            expiration_date__gte=today,
            expiration_date__lte=expiry_cutoff,
        )
    elif state == 'expired':
        medicines = medicines.filter(expiration_date__lt=today)

    medicines = medicines.order_by(
        F('expiration_date').asc(nulls_last=True),
        'name',
    )

    paginator = Paginator(medicines, 15)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'info/medicine_list.html', {
        'medicines': page,
        'categories': Medicine.CATEGORY_CHOICES,
        'query': query,
        'state': state,
        'category': category,
        'counts': counts,
        'today': today,
        'expiry_cutoff': expiry_cutoff,
        'expiry_window_days': MEDICINE_EXPIRY_WINDOW_DAYS,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def medicine_save_ajax(request):
    """Create or update a medicine cabinet item."""
    medicine_id = (request.POST.get('id') or '').strip()

    if medicine_id:
        if not medicine_id.isdigit():
            raise Http404('Medicine not found.')
        medicine = Medicine.objects.filter(pk=medicine_id, user=request.user).first()
        if medicine is None:
            raise Http404('Medicine not found.')
    else:
        medicine = Medicine(user=request.user)

    form = MedicineForm(request.POST, instance=medicine)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    medicine = form.save(commit=False)
    medicine.user = request.user
    medicine.save()

    return JsonResponse({
        'status': 'success',
        'message': (
            'Medicine updated successfully.' if medicine_id
            else 'Medicine added to the cabinet.'
        ),
        'id': medicine.pk,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def medicine_delete_ajax(request, pk):
    """Delete one of the user's medicine cabinet items."""
    medicine = Medicine.objects.filter(pk=pk, user=request.user).first()
    if medicine is None:
        raise Http404('Medicine not found.')

    name = medicine.name
    medicine.delete()
    return JsonResponse({
        'status': 'success',
        'message': f'Medicine "{name}" removed from the cabinet.',
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def medicine_restock_ajax(request):
    """Add stock to a medicine cabinet item."""
    medicine_id = (request.POST.get('id') or '').strip()
    amount_raw = (request.POST.get('amount') or '').strip()

    if not medicine_id.isdigit():
        raise Http404('Medicine not found.')

    medicine = Medicine.objects.filter(pk=medicine_id, user=request.user).first()
    if medicine is None:
        raise Http404('Medicine not found.')

    try:
        amount = Decimal(amount_raw)
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'error': 'Enter a valid restock amount.'}, status=400)

    if amount <= 0:
        return JsonResponse({'error': 'Restock amount must be greater than zero.'}, status=400)

    medicine.stock_quantity = (medicine.stock_quantity or 0) + amount
    medicine.save(update_fields=['stock_quantity'])

    return JsonResponse({
        'status': 'success',
        'message': f'Added {format(amount.normalize(), "f")} {medicine.unit} to {medicine.name}.',
        'stock_quantity': format(medicine.stock_quantity.normalize(), 'f'),
    })


@login_required(login_url='login')
def export_medicines_csv(request):
    """Export the user's medicine cabinet as a CSV file."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="medicine_cabinet.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Medicine',
        'Category',
        'Unit',
        'Stock',
        'Low Stock Threshold',
        'Expiration Date',
        'Notes',
    ])

    medicines = Medicine.objects.filter(user=request.user).order_by('name')
    for medicine in medicines:
        writer.writerow([
            medicine.name,
            medicine.category,
            medicine.unit,
            medicine.stock_quantity,
            medicine.low_stock_threshold,
            medicine.expiration_date or '',
            medicine.notes or '',
        ])

    return response


# --- 3-GENERATION PEDIGREE VIEWER & CERTIFICATE ---

def _build_lineage_node(user, tag):
    """Resolve a lineage node by tag number, returning bird metadata."""
    if not tag:
        return {'tag': 'Unknown', 'breed': 'N/A', 'gender': '', 'color': '', 'sire': '', 'dam': ''}
    bird = scoped_flock_members(user).filter(tag_number__iexact=tag.strip()).select_related('breed').first()
    if bird:
        return {
            'tag': bird.tag_number,
            'breed': bird.breed.name if bird.breed else 'N/A',
            'gender': bird.gender,
            'color': bird.color or '',
            'sire': bird.sire or '',
            'dam': bird.dam or '',
        }
    return {'tag': tag.strip(), 'breed': 'External / Unknown', 'gender': '', 'color': '', 'sire': '', 'dam': ''}


@login_required(login_url='login')
@_json_not_found
def pedigree_ajax(request, pk):
    """Retrieve full 3-generation lineage data for the pedigree modal."""
    bird = scoped_flock_member(request.user, pk)

    sire_node = _build_lineage_node(request.user, bird.sire)
    dam_node = _build_lineage_node(request.user, bird.dam)

    gp_pat_sire = _build_lineage_node(request.user, sire_node.get('sire'))
    gp_pat_dam = _build_lineage_node(request.user, sire_node.get('dam'))
    gp_mat_sire = _build_lineage_node(request.user, dam_node.get('sire'))
    gp_mat_dam = _build_lineage_node(request.user, dam_node.get('dam'))

    lineage = {
        'bird': {
            'tag': bird.tag_number,
            'breed': bird.breed.name if bird.breed else 'N/A',
            'gender': bird.gender,
            'color': bird.color or '',
            'birth_date': str(bird.birth_date) if bird.birth_date else '',
            'wins': bird.wins,
            'losses': bird.losses,
            'draws': bird.draws,
        },
        'sire': sire_node,
        'dam': dam_node,
        'grand_sire_paternal': gp_pat_sire['tag'],
        'grand_dam_paternal': gp_pat_dam['tag'],
        'grand_sire_maternal': gp_mat_sire['tag'],
        'grand_dam_maternal': gp_mat_dam['tag'],
        'gp_pat_sire': gp_pat_sire,
        'gp_pat_dam': gp_pat_dam,
        'gp_mat_sire': gp_mat_sire,
        'gp_mat_dam': gp_mat_dam,
    }
    return JsonResponse({'status': 'success', 'lineage': lineage})


@login_required(login_url='login')
def pedigree_certificate_page(request, pk):
    """Render a printable, official pedigree certificate for a bird."""
    bird = scoped_flock_member(request.user, pk)
    profile = getattr(request.user, 'profile', None)

    sire_node = _build_lineage_node(request.user, bird.sire)
    dam_node = _build_lineage_node(request.user, bird.dam)

    gp_pat_sire = _build_lineage_node(request.user, sire_node.get('sire'))
    gp_pat_dam = _build_lineage_node(request.user, sire_node.get('dam'))
    gp_mat_sire = _build_lineage_node(request.user, dam_node.get('sire'))
    gp_mat_dam = _build_lineage_node(request.user, dam_node.get('dam'))

    fights = bird.fight_records.order_by('-fight_date')[:5]

    return render(request, 'info/pedigree_certificate.html', {
        'bird': bird,
        'profile': profile,
        'sire': sire_node,
        'dam': dam_node,
        'gp_pat_sire': gp_pat_sire,
        'gp_pat_dam': gp_pat_dam,
        'gp_mat_sire': gp_mat_sire,
        'gp_mat_dam': gp_mat_dam,
        'fights': fights,
        'today': timezone.localdate(),
    })


# --- EXPORT & IMPORT TO CSV ---

@login_required(login_url='login')
def export_flock_csv(request):
    """Export the user's flock inventory into a downloadable CSV file."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="flock_inventory.csv"'
    response.write('\ufeff')  # BOM so Excel opens accented characters correctly.

    writer = csv.writer(response)
    writer.writerow([
        'Tag Number', 'Breed', 'Gender', 'Status',
        'Birth Date', 'Weight (g)', 'Wins', 'Losses', 'Draws',
        'Comb Type', 'Leg Color', 'Color', 'Cage Number',
        'Sire', 'Dam'
    ])

    members = scoped_flock_members(request.user).select_related('breed')
    for member in members:
        writer.writerow([
            member.tag_number,
            member.breed.name if member.breed else '',
            member.gender,
            member.status,
            member.birth_date or '',
            member.weight_grams or '',
            member.wins,
            member.losses,
            member.draws,
            member.comb_type or '',
            member.leg_color or '',
            member.color or '',
            member.cage_number or '',
            member.sire or '',
            member.dam or '',
        ])

    return response


@login_required(login_url='login')
@require_POST
def import_flock_csv(request):
    """Import flock members from an uploaded CSV spreadsheet."""
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.error(request, 'Please select a CSV file to upload.')
        return redirect('info:info_list')

    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Invalid file format. Please upload a .csv file.')
        return redirect('info:info_list')

    try:
        decoded = csv_file.read().decode('utf-8-sig')
    except Exception:
        messages.error(request, 'Could not read CSV file. Please ensure it is saved in UTF-8 format.')
        return redirect('info:info_list')

    reader = csv.DictReader(io.StringIO(decoded))
    imported_count = 0
    updated_count = 0
    row_errors = []

    with transaction.atomic():
        for row_idx, row in enumerate(reader, start=2):
            tag = (row.get('Tag Number') or row.get('tag_number') or '').strip()
            if not tag:
                continue

            gender = (row.get('Gender') or row.get('gender') or 'Cock').strip().capitalize()
            if gender not in ['Stag', 'Cock', 'Pullet', 'Hen']:
                gender = 'Cock'

            status = (row.get('Status') or row.get('status') or 'Active').strip().capitalize()
            if status not in ['Active', 'Conditioning', 'Broodcock', 'Broodhen', 'Retired']:
                status = 'Active'

            breed_name = (row.get('Breed') or row.get('breed') or '').strip()
            breed = None
            if breed_name:
                breed, _ = Breed.objects.get_or_create(name=breed_name)

            comb_type = (row.get('Comb Type') or row.get('comb_type') or 'Pea').strip()
            leg_color = (row.get('Leg Color') or row.get('leg_color') or 'Yellow').strip()
            color = (row.get('Color') or row.get('color') or '').strip()
            cage_number = (row.get('Cage Number') or row.get('cage_number') or '').strip()
            sire = (row.get('Sire') or row.get('sire') or '').strip()
            dam = (row.get('Dam') or row.get('dam') or '').strip()

            def _clean_int(val, default=0):
                try:
                    return max(0, int(val or default))
                except (ValueError, TypeError):
                    return default

            weight_grams = _clean_int(row.get('Weight (g)') or row.get('weight_grams'), None)
            wins = _clean_int(row.get('Wins') or row.get('wins'), 0)
            losses = _clean_int(row.get('Losses') or row.get('losses'), 0)
            draws = _clean_int(row.get('Draws') or row.get('draws'), 0)

            bird, created = FlockMember.objects.update_or_create(
                user=request.user,
                tag_number=tag,
                defaults={
                    'breed': breed,
                    'gender': gender,
                    'status': status,
                    'comb_type': comb_type,
                    'leg_color': leg_color,
                    'color': color,
                    'cage_number': cage_number,
                    'sire': sire,
                    'dam': dam,
                    'weight_grams': weight_grams,
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                }
            )
            if created:
                imported_count += 1
            else:
                updated_count += 1

    messages.success(request, f'CSV Import complete: {imported_count} new birds added, {updated_count} existing birds updated.')
    return redirect('info:info_list')


# --- BATCH ACTIONS ---

@login_required(login_url='login')
@require_POST
def flock_batch_action_ajax(request):
    """Execute batch status changes or batch health administration."""
    action = request.POST.get('action', '').strip()
    ids_raw = request.POST.getlist('ids[]') or request.POST.getlist('ids')

    if not ids_raw:
        return JsonResponse({'error': 'No birds selected.'}, status=400)

    birds = scoped_flock_members(request.user).filter(id__in=ids_raw)
    count = birds.count()

    if action == 'update_status':
        new_status = request.POST.get('status', '').strip()
        if new_status not in [c[0] for c in FlockMember.STATUS_CHOICES]:
            return JsonResponse({'error': 'Invalid status selected.'}, status=400)
        birds.update(status=new_status)
        return JsonResponse({'status': 'success', 'message': f'Updated {count} birds to "{new_status}".'})

    elif action == 'batch_health':
        record_type = request.POST.get('record_type', '').strip()
        title = request.POST.get('title', '').strip()
        date_administered = request.POST.get('date_administered', '').strip()
        next_due_date = request.POST.get('next_due_date', '').strip() or None
        notes = request.POST.get('notes', '').strip()

        if not title or not date_administered:
            return JsonResponse({'error': 'Title and administration date are required.'}, status=400)

        records_to_create = [
            HealthRecord(
                bird=b,
                record_type=record_type,
                title=title,
                date_administered=date_administered,
                next_due_date=next_due_date,
                notes=notes
            ) for b in birds
        ]
        HealthRecord.objects.bulk_create(records_to_create)
        return JsonResponse({'status': 'success', 'message': f'Logged "{title}" for {count} birds.'})

    elif action == 'delete':
        birds.delete()
        return JsonResponse({'status': 'success', 'message': f'Deleted {count} birds.'})

    return JsonResponse({'error': 'Unknown action.'}, status=400)
