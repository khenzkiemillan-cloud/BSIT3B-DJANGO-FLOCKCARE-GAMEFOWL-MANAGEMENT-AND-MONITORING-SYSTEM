from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import (
    FlockMember, HealthRecord, Medicine,
    WeightLog, BreedingPen, ClutchRecord,
)


class FlockMemberForm(forms.ModelForm):
    """Validate and save flock member records submitted from the UI."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for optional_field in ['weight_grams', 'comb_type', 'leg_color', 'color', 'cage_number', 'image', 'sire', 'dam', 'birth_date']:
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
            'image',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
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


class HealthRecordForm(forms.ModelForm):
    """Validate health and vaccination logs before saving them."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['medicine'].required = False
        self.fields['quantity_used'].required = False
        if self.user is not None and not getattr(self.user, 'is_anonymous', False):
            medicines = Medicine.objects.filter(user=self.user, item_type='medicine').order_by('name')
        else:
            medicines = Medicine.objects.none()
        self.fields['medicine'].queryset = medicines

    class Meta:
        model = HealthRecord
        fields = [
            'record_type', 'title', 'medicine', 'quantity_used',
            'date_administered', 'next_due_date', 'notes',
        ]
        widgets = {
            'date_administered': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
            'quantity_used': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
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

        medicine = cleaned_data.get('medicine')
        quantity = cleaned_data.get('quantity_used') or Decimal('0.00')
        if quantity is None:
            quantity = Decimal('0.00')
        if quantity < 0:
            self.add_error('quantity_used', 'Quantity used cannot be negative.')
        elif medicine and quantity <= 0:
            self.add_error(
                'quantity_used',
                'Enter how much medicine was used so it can be deducted from stock.',
            )
        elif medicine is None and quantity > 0:
            self.add_error(
                'medicine',
                'Select the medicine cabinet item that was used, or clear the quantity.',
            )
        cleaned_data['quantity_used'] = quantity
        return cleaned_data


class MedicineForm(forms.ModelForm):
    """Validate inventory items stored in the medicine cabinet, feeds, equipment, or supplies."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for optional_field in [
            'item_type',
            'low_stock_threshold',
            'expiration_date',
            'notes',
        ]:
            if optional_field in self.fields:
                self.fields[optional_field].required = False

    class Meta:
        model = Medicine
        fields = [
            'name',
            'item_type',
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
            raise forms.ValidationError('Item name is required.')
        return name

    def clean_item_type(self):
        item_type = (self.cleaned_data.get('item_type') or 'medicine').strip().lower()
        valid_types = [t[0] for t in Medicine.ITEM_TYPE_CHOICES]
        if item_type not in valid_types:
            item_type = 'medicine'
        return item_type

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
        if threshold is None:
            return Decimal('0.00')
        if threshold < 0:
            raise forms.ValidationError('Low stock threshold cannot be negative.')
        return threshold


InventoryItemForm = MedicineForm


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
