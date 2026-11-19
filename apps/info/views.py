from datetime import timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.scoping import scoped_flock_member, scoped_flock_members
from .choices import (
    COMMON_BREEDS, COMMON_MEDICINES, MEDICINE_UNITS, record_type_for_category,
)
from .forms import (
    FlockMemberForm, HealthRecordForm, MedicineForm,
    WeightLogForm, BreedingPenForm, ClutchRecordForm,
)
from .models import (
    Breed, FlockMember, HealthRecord, Medicine,
    WeightLog, BreedingPen, ClutchRecord,
)

HEALTH_DUE_WINDOW_DAYS = 30
MEDICINE_EXPIRY_WINDOW_DAYS = 30


class HealthStockError(Exception):
    """Raised when a health treatment cannot be deducted from cabinet stock."""


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


def _health_medicine_options(user):
    """Build the cabinet + common medicine list used by health record forms."""
    options = []
    seen = set()

    for medicine in Medicine.objects.filter(user=user).order_by('name'):
        name = (medicine.name or '').strip()
        key = name.casefold()
        if not name or key in seen:
            continue
        seen.add(key)
        options.append({
            'id': medicine.id,
            'name': name,
            'category': dict(Medicine.CATEGORY_CHOICES).get(
                medicine.category, medicine.category
            ),
            'record_type': record_type_for_category(medicine.category),
            'in_cabinet': True,
            'stock_quantity': medicine.stock_quantity,
            'unit': medicine.unit,
            'low_stock_threshold': medicine.low_stock_threshold,
        })

    for item in COMMON_MEDICINES:
        key = item['name'].casefold()
        if key in seen:
            continue
        seen.add(key)
        options.append({
            'id': None,
            'name': item['name'],
            'category': dict(Medicine.CATEGORY_CHOICES).get(
                item['category'], item['category']
            ),
            'record_type': item['record_type'],
            'in_cabinet': False,
            'stock_quantity': None,
            'unit': '',
            'low_stock_threshold': None,
        })

    return options


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


def _sync_latest_weight(bird):
    """Set the bird's stored weight to the most recent remaining weight log."""
    latest = bird.weight_logs.order_by('-date', '-created_at').first()
    bird.weight_grams = latest.weight_grams if latest else None
    bird.save(update_fields=['weight_grams'])
    return bird.weight_grams


def _format_quantity(quantity):
    """Render a stored decimal without trailing zeros."""
    return format(Decimal(quantity).normalize(), 'f')


def _adjust_health_medicine_stock(record, previous_medicine_id=None,
                                  previous_quantity=Decimal('0.00')):
    """Apply a health record's medicine usage to cabinet stock.

    The previous usage is restored first so that edits can increase, decrease,
    or change the medicine without losing stock. Call inside ``atomic()``.
    """
    if previous_medicine_id and previous_quantity:
        Medicine.objects.filter(pk=previous_medicine_id).update(
            stock_quantity=F('stock_quantity') + previous_quantity
        )

    if not record.medicine_id:
        return

    quantity = record.quantity_used or Decimal('0.00')
    if quantity <= 0:
        return

    medicine = (
        Medicine.objects.select_for_update()
        .filter(pk=record.medicine_id)
        .first()
    )
    if medicine is None:
        raise HealthStockError(
            'The selected medicine is no longer in your cabinet.'
        )
    if medicine.stock_quantity < quantity:
        raise HealthStockError(
            f'Not enough {medicine.name} in stock. '
            f'Available: {_format_quantity(medicine.stock_quantity)} {medicine.unit}.'
        )

    medicine.stock_quantity -= quantity
    medicine.save(update_fields=['stock_quantity'])


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
        retired=Count('id', filter=Q(status='Retired')),
        sold=Count('id', filter=Q(status='Sold')),
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
    bird_tags = list(
        members_list.order_by('tag_number').values_list('tag_number', flat=True)
    )

    return render(request, 'info/info_list.html', {
        'members': members,
        'breeds': breeds,
        'common_breeds': COMMON_BREEDS,
        'bird_tags': bird_tags,
        'farm_birds': scoped_flock_members(request.user).order_by('tag_number'),
        'medicine_options': _health_medicine_options(request.user),
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


# --- BREEDS ---

@login_required(login_url='login')
@require_POST
def breed_create_ajax(request):
    """Create a breed now so it can be selected in the dropdown immediately."""
    name = (request.POST.get('name') or '').strip()
    if not name:
        return JsonResponse({'error': 'Enter a breed name.'}, status=400)
    if len(name) > 100:
        return JsonResponse({'error': 'Breed name must be 100 characters or fewer.'}, status=400)

    breed = Breed.objects.filter(name__iexact=name).first()
    created = False
    if breed is None:
        breed = Breed.objects.create(name=name)
        created = True

    return JsonResponse({
        'status': 'success',
        'id': breed.pk,
        'name': breed.name,
        'created': created,
        'message': (
            f'Breed "{breed.name}" added and selected.'
            if created else f'Breed "{breed.name}" already exists and was selected.'
        ),
    })


# --- WEIGHT LOGS ---

@login_required(login_url='login')
@_json_not_found
def weight_logs_ajax(request, pk):
    """Retrieve the weight history for a bird."""
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

    # The bird's headline weight should always come from the newest log, even
    # when this submission is backdated.
    current_weight = _sync_latest_weight(bird)

    return JsonResponse({
        'status': 'success',
        'message': f'Logged {log.weight_grams}g on {log.date}.',
        'weight_grams': current_weight,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def weight_log_delete_ajax(request, pk):
    """Delete a weight log and re-sync the bird's latest weight."""
    log = WeightLog.objects.filter(pk=pk, bird__user=request.user).first()
    if log is None:
        raise Http404('Weight log not found.')
    bird = log.bird
    log.delete()
    current_weight = _sync_latest_weight(bird)
    return JsonResponse({
        'status': 'success',
        'message': 'Weight log deleted.',
        'weight_grams': current_weight,
    })


# --- BREEDING & CLUTCH VIEWS ---

@login_required(login_url='login')
def breeding_list_page(request):
    """Render breeding pens and clutch hatch tracking."""
    pens = BreedingPen.objects.filter(user=request.user).select_related('sire', 'dam').prefetch_related('clutches')
    members = scoped_flock_members(request.user).select_related('breed')
    cocks = members.filter(gender__in=['Cock', 'Stag']).order_by('tag_number')
    hens = members.filter(gender__in=['Hen', 'Pullet']).order_by('tag_number')

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

    form = BreedingPenForm(request.POST, instance=pen, user=request.user)
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
    records = bird.health_records.select_related('medicine').order_by('-date_administered')
    data = [{
        'id': record.id,
        'record_type': record.record_type,
        'title': record.title,
        'medicine': record.medicine_id,
        'medicine_name': record.medicine.name if record.medicine else '',
        'medicine_unit': record.medicine.unit if record.medicine else '',
        'quantity_used': _format_quantity(record.quantity_used) if record.quantity_used else '',
        'date_administered': str(record.date_administered),
        'next_due_date': str(record.next_due_date) if record.next_due_date else '',
        'notes': record.notes or '',
    } for record in records]
    return JsonResponse({'bird_tag': bird.tag_number, 'data': data})


@login_required(login_url='login')
@require_POST
@_json_not_found
def health_record_save_ajax(request):
    """Create or update a health log and adjust medicine stock."""
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

    previous_medicine_id = record.medicine_id if record else None
    previous_quantity = (record.quantity_used or Decimal('0.00')) if record else Decimal('0.00')

    form = HealthRecordForm(request.POST, instance=record, user=request.user)
    if not form.is_valid():
        return JsonResponse(
            {'error': _form_error_message(form), 'errors': form.errors.get_json_data()},
            status=400,
        )

    record = form.save(commit=False)
    record.bird = bird

    try:
        with transaction.atomic():
            record.save()
            _adjust_health_medicine_stock(
                record,
                previous_medicine_id=previous_medicine_id,
                previous_quantity=previous_quantity,
            )
    except HealthStockError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    message = (
        'Health record updated successfully.' if record_id
        else 'Health record added successfully.'
    )
    if record.medicine_id and record.quantity_used:
        message += (
            f' Deducted {_format_quantity(record.quantity_used)} '
            f'{record.medicine.unit} of {record.medicine.name} from stock.'
        )

    return JsonResponse({
        'status': 'success',
        'message': message,
        'id': record.pk,
    })


@login_required(login_url='login')
@require_POST
@_json_not_found
def health_record_delete_ajax(request, pk):
    """Delete a health record and restore any medicine stock it used."""
    record = HealthRecord.objects.filter(pk=pk, bird__user=request.user).first()
    if record is None:
        raise Http404('Health record not found.')

    title = record.title
    medicine_id = record.medicine_id
    quantity_used = record.quantity_used or Decimal('0.00')

    with transaction.atomic():
        record.delete()
        if medicine_id and quantity_used > 0:
            # The cabinet item may already be gone (FK is SET_NULL), in which
            # case there is no stock left to restore.
            Medicine.objects.filter(pk=medicine_id).update(
                stock_quantity=F('stock_quantity') + quantity_used
            )

    message = f'Health record "{title}" deleted successfully.'
    if medicine_id and quantity_used > 0:
        message += ' Medicine stock was returned to the cabinet.'

    return JsonResponse({
        'status': 'success',
        'message': message,
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

    records = HealthRecord.objects.filter(bird__user=request.user).select_related('bird', 'medicine')
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
        'medicine_options': _health_medicine_options(request.user),
        'query': query,
        'state': state,
        'record_type': record_type,
        'counts': counts,
        'today': today,
        'due_cutoff': due_cutoff,
        'due_window_days': HEALTH_DUE_WINDOW_DAYS,
    })



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
        'birds': scoped_flock_members(request.user).order_by('tag_number'),
        'categories': Medicine.CATEGORY_CHOICES,
        'medicine_suggestions': COMMON_MEDICINES,
        'unit_suggestions': MEDICINE_UNITS,
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

    if not amount.is_finite():
        return JsonResponse({'error': 'Enter a valid restock amount.'}, status=400)

    try:
        amount = amount.quantize(Decimal('0.01'))
    except InvalidOperation:
        return JsonResponse({'error': 'Enter a valid restock amount.'}, status=400)

    if amount <= 0:
        return JsonResponse({'error': 'Restock amount must be greater than zero.'}, status=400)

    new_stock = (medicine.stock_quantity or 0) + amount
    if new_stock > Decimal('99999999.99'):
        return JsonResponse({'error': 'That restock would exceed the maximum stock quantity.'}, status=400)

    with transaction.atomic():
        medicine.stock_quantity = new_stock
        medicine.save(update_fields=['stock_quantity'])

    message = f'Added {format(amount.normalize(), "f")} {medicine.unit} to {medicine.name}.'
    return JsonResponse({
        'status': 'success',
        'message': message,
        'stock_quantity': format(medicine.stock_quantity.normalize(), 'f'),
    })



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

    return render(request, 'info/pedigree_certificate.html', {
        'bird': bird,
        'profile': profile,
        'sire': sire_node,
        'dam': dam_node,
        'gp_pat_sire': gp_pat_sire,
        'gp_pat_dam': gp_pat_dam,
        'gp_mat_sire': gp_mat_sire,
        'gp_mat_dam': gp_mat_dam,
        'today': timezone.localdate(),
    })


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
        form = HealthRecordForm(request.POST, user=request.user)
        if not form.is_valid():
            return JsonResponse({'error': _form_error_message(form)}, status=400)

        cleaned_data = form.cleaned_data
        medicine = cleaned_data.get('medicine')
        quantity_used = cleaned_data.get('quantity_used') or Decimal('0.00')
        total_needed = quantity_used * count

        try:
            with transaction.atomic():
                if medicine is not None and total_needed > 0:
                    cabinet_item = (
                        Medicine.objects.select_for_update()
                        .filter(pk=medicine.pk, user=request.user)
                        .first()
                    )
                    if cabinet_item is None:
                        raise HealthStockError(
                            'The selected medicine is no longer in your cabinet.'
                        )
                    if cabinet_item.stock_quantity < total_needed:
                        raise HealthStockError(
                            f'Not enough {cabinet_item.name} in stock for {count} birds. '
                            f'Needed: {_format_quantity(total_needed)} {cabinet_item.unit}, '
                            f'available: {_format_quantity(cabinet_item.stock_quantity)} '
                            f'{cabinet_item.unit}.'
                        )
                    cabinet_item.stock_quantity -= total_needed
                    cabinet_item.save(update_fields=['stock_quantity'])

                records_to_create = [
                    HealthRecord(bird=b, **cleaned_data) for b in birds
                ]
                HealthRecord.objects.bulk_create(records_to_create)
        except HealthStockError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        message = f'Logged "{cleaned_data["title"]}" for {count} birds.'
        if medicine is not None and total_needed > 0:
            message += (
                f' Deducted {_format_quantity(total_needed)} {medicine.unit} '
                f'of {medicine.name} from stock.'
            )
        return JsonResponse({
            'status': 'success',
            'message': message,
        })

    elif action == 'delete':
        birds.delete()
        return JsonResponse({'status': 'success', 'message': f'Deleted {count} birds.'})

    return JsonResponse({'error': 'Unknown action.'}, status=400)
