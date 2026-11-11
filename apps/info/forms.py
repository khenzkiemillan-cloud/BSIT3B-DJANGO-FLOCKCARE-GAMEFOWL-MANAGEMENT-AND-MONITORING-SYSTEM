from django import forms

from .models import (
    FlockMember, HealthRecord, Medicine,
    FightRecord, WeightLog, BreedingPen, ClutchRecord
)


class FlockMemberForm(forms.ModelForm):
    """Validate and save flock member records submitted from the UI."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for optional_field in ['wins', 'losses', 'draws', 'weight_grams', 'comb_type', 'leg_color', 'color', 'cage_number', 'image', 'sire', 'dam', 'birth_date']:
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


class BreedingPenForm(forms.ModelForm):
    class Meta:
        model = BreedingPen
        fields = ['pen_number', 'sire', 'dam', 'date_paired', 'date_separated', 'status', 'notes']
        widgets = {
            'date_paired': forms.DateInput(attrs={'type': 'date'}),
            'date_separated': forms.DateInput(attrs={'type': 'date'}),
        }


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
