import csv
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.scoping import scoped_flock_member, scoped_flock_members
from .forms import FlockMemberForm, HealthRecordForm
from .models import Breed, FlockMember, HealthRecord


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
            Q(dam__icontains=query)
        )

    if status == 'breeding':
        members_list = members_list.filter(status__in=['Broodcock', 'Broodhen'])
    elif status:
        members_list = members_list.filter(status=status)

    paginator = Paginator(members_list, 10)
    page_number = request.GET.get('page', 1)
    members = paginator.get_page(page_number)
    breeds = Breed.objects.all()

    return render(request, 'info/info_list.html', {
        'members': members,
        'breeds': breeds,
        'query': query,
        'status': status,
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
            Q(dam__icontains=query)
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
        'weight_grams': bird.weight_grams,
        'wins': bird.wins,
        'losses': bird.losses,
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

    form = FlockMemberForm(request.POST, instance=bird)
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


# --- PEDIGREE VIEWER ---

@login_required(login_url='login')
@_json_not_found
def pedigree_ajax(request, pk):
    """Retrieve lineage data for the pedigree modal."""
    bird = scoped_flock_member(request.user, pk)

    # Check if sire and dam exist as flock members
    sire_obj = scoped_flock_members(request.user).filter(tag_number=bird.sire).first() if bird.sire else None
    dam_obj = scoped_flock_members(request.user).filter(tag_number=bird.dam).first() if bird.dam else None

    lineage = {
        'bird': {'tag': bird.tag_number, 'breed': bird.breed.name if bird.breed else 'N/A', 'gender': bird.gender},
        'sire': {'tag': bird.sire or 'Unknown', 'breed': sire_obj.breed.name if sire_obj and sire_obj.breed else 'N/A'},
        'dam': {'tag': bird.dam or 'Unknown', 'breed': dam_obj.breed.name if dam_obj and dam_obj.breed else 'N/A'},
        'grand_sire_paternal': sire_obj.sire if sire_obj else 'Unknown',
        'grand_dam_paternal': sire_obj.dam if sire_obj else 'Unknown',
        'grand_sire_maternal': dam_obj.sire if dam_obj else 'Unknown',
        'grand_dam_maternal': dam_obj.dam if dam_obj else 'Unknown',
    }
    return JsonResponse({'status': 'success', 'lineage': lineage})


# --- EXPORT TO CSV ---

@login_required(login_url='login')
def export_flock_csv(request):
    """Export the user's flock inventory into a downloadable CSV file."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="flock_inventory.csv"'
    response.write('\ufeff')  # BOM so Excel opens accented characters correctly.

    writer = csv.writer(response)
    writer.writerow(['Tag Number', 'Breed', 'Gender', 'Status', 'Birth Date', 'Weight (g)', 'Wins', 'Losses', 'Sire', 'Dam'])

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
            member.sire or '',
            member.dam or '',
        ])

    return response
