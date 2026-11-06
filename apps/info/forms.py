from django import forms

from .models import FlockMember, HealthRecord


class FlockMemberForm(forms.ModelForm):
    """Validate and save flock member records submitted from the UI."""

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
            'weight_grams',
            'wins',
            'losses',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_tag_number(self):
        tag_number = (self.cleaned_data.get('tag_number') or '').strip()
        if not tag_number:
            raise forms.ValidationError('Tag number is required.')

        duplicate = FlockMember.objects.filter(tag_number__iexact=tag_number)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError('A flock member with this tag number already exists.')

        return tag_number

    def clean_sire(self):
        return (self.cleaned_data.get('sire') or '').strip()

    def clean_dam(self):
        return (self.cleaned_data.get('dam') or '').strip()


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
