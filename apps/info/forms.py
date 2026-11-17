from datetime import timedelta

from django import forms
from django.utils import timezone

from .choices import CONDITIONING_PROGRAMS
from .models import (
    FlockMember, HealthRecord, Medicine,
    FightRecord, WeightLog, BreedingPen, ClutchRecord, FinancialEntry,
    ConditioningSession,
)


def _validate_conditioning_values(cleaned_data, add_error):
    """Reject impossible or likely-typo conditioning dates and weights."""
    today = timezone.localdate()
    start_date = cleaned_data.get('conditioning_start_date')
    target_date = cleaned_data.get('conditioning_target_date')
    target_weight = cleaned_data.get('target_weight_grams')
    current_weight = cleaned_data.get('weight_grams')

    if start_date and start_date > today:
        add_error(
            'conditioning_start_date',
            'Conditioning start date cannot be in the future.',
        )

    if target_date and start_date and target_date <= start_date:
        add_error(
            'conditioning_target_date',
            'Target date must be after the conditioning start date.',
        )

    if target_date and target_date > today + timedelta(days=365):
        add_error(
            'conditioning_target_date',
            'Target date must be within the next year.',
        )

    if target_weight and current_weight:
        if abs(target_weight - current_weight) > current_weight * 0.5:
            add_error(
                'target_weight_grams',
                'Target weight must be within 50% of the current weight. '
                'Check the numbers before saving.',
            )


class ConditioningForm(forms.Form):
    """Validate the conditioning requirements for an existing bird."""

    conditioning_start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    conditioning_target_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    target_weight_grams = forms.IntegerField(min_value=1)
    conditioning_program = forms.ChoiceField(
        choices=[(program, program) for program in CONDITIONING_PROGRAMS] + [
            ('Custom', 'Custom / other program'),
        ],
    )
    conditioning_program_custom = forms.CharField(
        max_length=100, required=False,
    )
    conditioning_feed_plan = forms.CharField(max_length=255)
    weight_grams = forms.IntegerField(min_value=0, required=False)
    conditioning_phase = forms.ChoiceField(
        choices=FlockMember.CONDITIONING_PHASES,
        required=False,
        initial='foundation',
    )
    conditioning_notes = forms.CharField(
        max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('conditioning_program') == 'Custom':
            custom = (cleaned_data.get('conditioning_program_custom') or '').strip()
            if not custom:
                self.add_error(
                    'conditioning_program_custom',
                    'Enter the custom conditioning program.',
                )
            else:
                cleaned_data['conditioning_program'] = custom

        if not cleaned_data.get('conditioning_phase'):
            cleaned_data['conditioning_phase'] = 'foundation'

        cleaned_data['conditioning_feed_plan'] = (
            cleaned_data.get('conditioning_feed_plan') or ''
        ).strip()
        cleaned_data['conditioning_notes'] = (
            cleaned_data.get('conditioning_notes') or ''
        ).strip()
        _validate_conditioning_values(cleaned_data, self.add_error)
        return cleaned_data


class FlockMemberForm(forms.ModelForm):
    """Validate and save flock member records submitted from the UI."""

    # Filled in on the Conditioning tab. They only become mandatory once the
    # bird's status is set to Conditioning, so Active/Retired birds can still
    # be saved without a conditioning plan.
    CONDITIONING_REQUIRED_FIELDS = [
        ('conditioning_start_date', 'Conditioning start date'),
        ('target_weight_grams', 'Target / fight weight'),
        ('conditioning_program', 'Conditioning program'),
        ('conditioning_feed_plan', 'Feed / diet plan'),
    ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for optional_field in ['wins', 'losses', 'draws', 'weight_grams', 'comb_type', 'leg_color', 'color', 'cage_number', 'image', 'sire', 'dam', 'birth_date', 'conditioning_start_date', 'target_weight_grams', 'conditioning_program', 'conditioning_feed_plan', 'conditioning_target_date', 'conditioning_notes']:
            if optional_field in self.fields:
                self.fields[optional_field].required = False

    class Meta:
        model = FlockMember
        fields = [
            'tag_number',
            'breed',
            'gender',
            'birth_date',
            'sire',
            'dam',
            'status',
            'comb_type',
            'leg_color',
            'color',
            'cage_number',
            'weight_grams',
            'wins',
            'losses',
            'draws',
            'conditioning_start_date',
            'conditioning_target_date',
            'target_weight_grams',
            'conditioning_program',
            'conditioning_feed_plan',
            'conditioning_phase',
            'conditioning_notes',
            'image',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'conditioning_start_date': forms.DateInput(attrs={'type': 'date'}),
            'conditioning_target_date': forms.DateInput(attrs={'type': 'date'}),
            'conditioning_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_tag_number(self):
        tag_number = (self.cleaned_data.get('tag_number') or '').strip()
        if not tag_number:
            raise forms.ValidationError('Tag number is required.')

        user = getattr(self.instance, 'user', None) or self.user
        duplicate = FlockMember.objects.filter(tag_number__iexact=tag_number)
        if user and not getattr(user, 'is_anonymous', False):
            duplicate = duplicate.filter(user=user)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError('A flock member with this tag number already exists in your flock.')

        return tag_number

    def clean_sire(self):
        return (self.cleaned_data.get('sire') or '').strip()

    def clean_dam(self):
        return (self.cleaned_data.get('dam') or '').strip()

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('status') == 'Conditioning':
            for field_name, label in self.CONDITIONING_REQUIRED_FIELDS:
                value = cleaned_data.get(field_name)
                if value in (None, ''):
                    self.add_error(
                        field_name,
                        f'{label} is required when the bird is in conditioning.',
                    )

        for field_name in ('conditioning_program', 'conditioning_feed_plan'):
            if cleaned_data.get(field_name) is not None:
                cleaned_data[field_name] = cleaned_data[field_name].strip()

        if not cleaned_data.get('conditioning_phase'):
            cleaned_data['conditioning_phase'] = 'foundation'

        _validate_conditioning_values(cleaned_data, self.add_error)
        return cleaned_data

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'name'):
            valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
            if not image.name.lower().endswith(valid_exts):
                raise forms.ValidationError('Uploaded file must be an image (JPG, PNG, WebP).')
            # 5MB limit
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file must be under 5 MB.')
        return image


class ConditioningSessionForm(forms.ModelForm):
    """Validate a planned or completed step in a bird's conditioning plan."""

    class Meta:
        model = ConditioningSession
        fields = [
            'phase', 'session_type', 'title', 'scheduled_date',
            'status', 'duration_minutes', 'notes',
        ]
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise forms.ValidationError('Session title is required.')
        return title

    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date > timezone.localdate() + timedelta(days=365):
            raise forms.ValidationError('Schedule sessions within the next year.')
        return scheduled_date


class HealthRecordForm(forms.ModelForm):
    """Validate health and vaccination logs before saving them."""

    class Meta:
        model = HealthRecord
        fields = ['record_type', 'title', 'date_administered', 'next_due_date', 'notes']
        widgets = {
            'date_administered': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise forms.ValidationError('Title is required.')
        return title

    def clean(self):
        cleaned_data = super().clean()
        date_administered = cleaned_data.get('date_administered')
        next_due_date = cleaned_data.get('next_due_date')
        if date_administered and next_due_date and next_due_date < date_administered:
            self.add_error('next_due_date', 'Next due date cannot be before the date administered.')
        return cleaned_data


class MedicineForm(forms.ModelForm):
    """Validate medicine inventory items stored in the flock's cabinet."""

    class Meta:
        model = Medicine
        fields = [
            'name',
            'category',
            'unit',
            'stock_quantity',
            'low_stock_threshold',
            'expiration_date',
            'notes',
        ]
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'low_stock_threshold': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Medicine name is required.')
        return name

    def clean_unit(self):
        unit = (self.cleaned_data.get('unit') or '').strip()
        if not unit:
            raise forms.ValidationError('Unit is required.')
        return unit

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is None or stock_quantity < 0:
            raise forms.ValidationError('Stock quantity cannot be negative.')
        return stock_quantity

    def clean_low_stock_threshold(self):
        threshold = self.cleaned_data.get('low_stock_threshold')
        if threshold is None or threshold < 0:
            raise forms.ValidationError('Low stock threshold cannot be negative.')
        return threshold


class FightRecordForm(forms.ModelForm):
    class Meta:
        model = FightRecord
        fields = [
            'event_name', 'fight_date', 'weight_grams',
            'opponent', 'gaff_type', 'result',
            'duration_seconds', 'video_url', 'notes'
        ]
        widgets = {
            'fight_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_event_name(self):
        name = (self.cleaned_data.get('event_name') or '').strip()
        if not name:
            raise forms.ValidationError('Event name is required.')
        return name


class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['date', 'time_of_day', 'weight_grams', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.localdate():
            raise forms.ValidationError('Weight log date cannot be in the future.')
        return date

    def clean_weight_grams(self):
        weight = self.cleaned_data.get('weight_grams')
        if weight is not None and weight > 20000:
            raise forms.ValidationError('Enter a realistic weight in grams.')
        return weight


class BreedingPenForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Only let a breeder pair their own birds. Without this a crafted POST
        # could reference another user's flock member.
        if self.user is not None and not getattr(self.user, 'is_anonymous', False):
            members = FlockMember.objects.filter(user=self.user)
        else:
            members = FlockMember.objects.none()
        self.fields['sire'].queryset = members
        self.fields['dam'].queryset = members

    class Meta:
        model = BreedingPen
        fields = ['pen_number', 'sire', 'dam', 'date_paired', 'date_separated', 'status', 'notes']
        widgets = {
            'date_paired': forms.DateInput(attrs={'type': 'date'}),
            'date_separated': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_pen_number(self):
        pen_number = (self.cleaned_data.get('pen_number') or '').strip()
        if not pen_number:
            raise forms.ValidationError('Pen number is required.')
        return pen_number

    def clean(self):
        cleaned_data = super().clean()
        sire = cleaned_data.get('sire')
        dam = cleaned_data.get('dam')
        date_paired = cleaned_data.get('date_paired')
        date_separated = cleaned_data.get('date_separated')

        if sire and dam and sire.pk == dam.pk:
            raise forms.ValidationError('The sire and dam must be two different birds.')

        if sire and sire.gender not in ('Cock', 'Stag'):
            self.add_error('sire', 'Select a cock or stag as the sire.')

        if dam and dam.gender not in ('Hen', 'Pullet'):
            self.add_error('dam', 'Select a hen or pullet as the dam.')

        if date_paired and date_separated and date_separated < date_paired:
            self.add_error('date_separated', 'Separation date cannot be before the pairing date.')

        return cleaned_data


class ClutchRecordForm(forms.ModelForm):
    class Meta:
        model = ClutchRecord
        fields = [
            'clutch_number', 'date_started', 'eggs_collected',
            'fertile_eggs', 'hatched_count', 'hatch_date', 'notes'
        ]
        widgets = {
            'date_started': forms.DateInput(attrs={'type': 'date'}),
            'hatch_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        eggs = cleaned_data.get('eggs_collected') or 0
        fertile = cleaned_data.get('fertile_eggs') or 0
        hatched = cleaned_data.get('hatched_count') or 0
        date_started = cleaned_data.get('date_started')
        hatch_date = cleaned_data.get('hatch_date')

        if fertile > eggs:
            self.add_error('fertile_eggs', 'Fertile eggs cannot exceed eggs collected.')

        if hatched > fertile:
            self.add_error('hatched_count', 'Hatched chicks cannot exceed fertile eggs.')

        if date_started and hatch_date and hatch_date < date_started:
            self.add_error('hatch_date', 'Hatch date cannot be before the date started.')

        return cleaned_data


class FinancialEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user is not None and not getattr(self.user, 'is_anonymous', False):
            self.fields['bird'].queryset = FlockMember.objects.filter(user=self.user).order_by('tag_number')
        else:
            self.fields['bird'].queryset = FlockMember.objects.none()
        self.fields['bird'].required = False

    class Meta:
        model = FinancialEntry
        fields = ['entry_type', 'category', 'amount', 'date', 'description', 'bird', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

    def clean_description(self):
        description = (self.cleaned_data.get('description') or '').strip()
        if not description:
            raise forms.ValidationError('Description is required.')
        return description

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        entry_type = cleaned_data.get('entry_type')
        category = cleaned_data.get('category')
        if entry_type and category:
            valid = FinancialEntry.EXPENSE_CATEGORIES if entry_type == FinancialEntry.TYPE_EXPENSE else FinancialEntry.INCOME_CATEGORIES
            valid_keys = {k for k, _ in valid}
            if category not in valid_keys:
                cleaned_data['category'] = 'Other' if entry_type == FinancialEntry.TYPE_EXPENSE else 'Other'
        return cleaned_data
